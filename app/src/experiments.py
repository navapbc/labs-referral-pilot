import argparse
import json
import logging
from pprint import pformat
from typing import Any, Dict

from phoenix.client import Client
from phoenix.client.experiments import run_experiment
from phoenix.client.resources.datasets import Dataset
from phoenix.client.resources.experiments.types import TaskOutput

from src.common import phoenix_utils
from src.pipelines.generate_referrals.pipeline_wrapper import PipelineWrapper

logger = logging.getLogger(__name__)


def get_sets(output: TaskOutput, expected: Dict[str, Any]) -> tuple[set[str], set[str]]:
    assert isinstance(output, dict), f"Expected dict, but got {type(output)}: {pformat(output)}"
    assert len(output["content"]) == 1, pformat(output["content"])
    output_obj = json.loads(output["content"][0]["text"])
    # Extract only the names of the resources from the output
    output_set = set([resource["name"] for resource in output_obj["resources"]])

    expected_json_str = expected[OUTPUT_COLUMN_NAME]
    expected_obj = json.loads(expected_json_str)
    expectation_set = set(expected_obj["expected_referrals"])

    return output_set, expectation_set


def precision(output: TaskOutput, expected: Dict[str, Any]) -> float:
    output_set, expectation_set = get_sets(output, expected)
    return len(output_set.intersection(expectation_set)) / len(expectation_set)


def accuracy(output: TaskOutput, expected: Dict[str, Any]) -> float:
    output_set, expectation_set = get_sets(output, expected)
    return len(output_set.intersection(expectation_set)) / len(output_set)


pipeline_wrapper = PipelineWrapper()
pipeline_wrapper.setup()


def get_answer(example: dict) -> TaskOutput:
    question_json_str = example["input"][INPUT_COLUMN_NAME]
    question_obj = json.loads(question_json_str)
    question = question_obj["caseworker_input"]
    logger.info("Getting answer for: %r", question)

    # if not True:
    #     import random
    #     answers = [
    #         "All Saints Episcopal Church",
    #         "Travis County Family Support Services",
    #         "First Baptist Church of Austin",
    #         "Central Presbyterian Church",
    #     ]
    #     rand_answers = random.sample(answers, k=random.randint(1, len(answers)))
    #     # print(f"Random answers: {rand_answers}")
    #     return ", ".join(rand_answers)

    response = pipeline_wrapper.run_api(query=question)
    assert len(response["llm"]["replies"]) == 1, pformat(response)
    return response["llm"]["replies"][0].to_dict()


def run(dataset: Dataset, client: Client) -> None:
    run_experiment(
        dataset=dataset,
        task=get_answer,
        evaluators=[precision, accuracy],
        client=client,
    )


INPUT_COLUMN_NAME = "Input"
OUTPUT_COLUMN_NAME = "Output"


def export_dataset(dataset_name: str, filename: str, client: Client) -> None:
    "Retrieve a dataset by name and save it as a CSV file. Useful for exporting a dataset from the deployed Phoenix."
    try:
        dataset = client.datasets.get_dataset(dataset=dataset_name)
        # Convert the dataset to a pandas DataFrame to save as CSV
        df = dataset.to_dataframe()

        # Remove the extraneous 'input' and 'output' keys and just keep the values
        # This ensures that when the CSV file is imported, the input and output columns are the same as in the deployed Phoenix
        df[INPUT_COLUMN_NAME] = df["input"].apply(lambda x: x[INPUT_COLUMN_NAME])
        df[OUTPUT_COLUMN_NAME] = df["output"].apply(lambda x: x[OUTPUT_COLUMN_NAME])
        # Convert metadata to JSON string so it can be correctly parsed when running experiments if needed
        df["metadata"] = df["metadata"].apply(lambda x: json.dumps(x))
        df = df[[INPUT_COLUMN_NAME, OUTPUT_COLUMN_NAME, "metadata"]]
        df.to_csv(filename, index=False)
    except ValueError as e:
        logger.error("Error retrieving dataset: %s", e)
        print_datasets(client)


def print_datasets(client: Client) -> list:
    all_datasets = client.datasets.list()
    logger.info("%d available datasets:\n%s", len(all_datasets), pformat(all_datasets))
    return all_datasets


def import_dataset(client: Client, filename: str, dataset_name: str) -> Any:
    """
    Import a dataset from a CSV file into Phoenix.
    Useful for loading dataset locally to test experiments.
    Reminder to reduce the number of rows in the CSV file for development.
    """
    return client.datasets.create_dataset(
        name=dataset_name,
        csv_file_path=filename,
        input_keys=[INPUT_COLUMN_NAME],
        output_keys=[OUTPUT_COLUMN_NAME],
        # Caution: Note that the metadata column is different than on the deployed Phoenix
        # In the Phoenix UI, click on each example to compare -- don't compare in the table view
        metadata_keys=["metadata"],
    )


def main() -> None:
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=str, default="brandon2")
    parser.add_argument(
        "action",
        type=str,
        choices=["export", "import", "run", "run_on_deployed", ""],
        default="run",
    )
    args = parser.parse_args()

    action = args.action if args.action else "run"
    logger.info("Action=%s Dataset=%r", action, args.dataset)

    if action == "export":
        client_to_deployed_phx = phoenix_utils.client_to_deployed_phoenix()
        export_dataset(args.dataset, "dataset.csv", client_to_deployed_phx)
        return

    client = phoenix_utils._create_client()
    if action == "import":
        import_dataset(client, "dataset.csv", args.dataset)
        return

    if action == "run_on_deployed":
        logger.info("Running experiment on deployed Phoenix")
        client = phoenix_utils.client_to_deployed_phoenix()

    try:
        # Get the dataset, run the experiment, and post the results
        dataset = client.datasets.get_dataset(dataset=args.dataset)
        run(dataset, client)
        print("Experiment complete. Check results in the Phoenix UI.")
    except ValueError as e:
        logger.error("Error retrieving dataset: %s", e)
        print_datasets(client)
