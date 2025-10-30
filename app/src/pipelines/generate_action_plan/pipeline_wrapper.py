import logging

from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from openinference.instrumentation import using_attributes
from pydantic import BaseModel

from src.common import haystack_utils
from src.common.components import OpenAIWebSearchGenerator
from src.pipelines.generate_referrals.pipeline_wrapper import Resource

logger = logging.getLogger(__name__)


class ActionPlan(BaseModel):
    title: str
    summary: str
    content: str


action_plan_as_json = """
{
    "title": string,
    "summary": string,
    "content": string
}
"""


def create_websearch() -> OpenAIWebSearchGenerator:
    return OpenAIWebSearchGenerator()


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_action_plan"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("llm", create_websearch())

        prompt_template = haystack_utils.get_phoenix_prompt("generate_action_plan")
        pipeline.add_component(
            instance=ChatPromptBuilder(
                template=prompt_template, required_variables=["resources", "action_plan_json"]
            ),
            name="prompt_builder",
        )
        pipeline.connect("prompt_builder", "llm.messages")

        self.pipeline = pipeline

    # Called for the `generate-action-plan/run` endpoint
    def run_api(self, resources: list[Resource] | list[dict], user_email: str) -> dict:
        resource_objects = get_resources(resources)

        with using_attributes(user_id=user_email):
            response = self.pipeline.run(
                {
                    "prompt_builder": {
                        "resources": format_resources(resource_objects),
                        "action_plan_json": action_plan_as_json,
                    },
                    "llm": {"model": "gpt-5-mini", "reasoning_effort": "low"},
                }
            )
            # logger.info("Results: %s", pformat(response["response"], width=160))
            return response


def get_resources(resources: list[Resource] | list[dict]) -> list[Resource]:
    """Ensure we have a list of Resource objects."""
    if not resources:
        return []
    if isinstance(resources[0], Resource):
        return resources  # type: ignore[return-value]
    return [Resource(**res) for res in resources]  # type: ignore[arg-type]


def format_resources(resources: list[Resource]) -> str:
    """Format a list of Resource objects into a readable string."""
    formatted_resources = []
    for resource in resources:
        resource_str = f"Name: {resource.name}\n"
        if resource.description:
            resource_str += f"- Description: {resource.description}\n"
        if resource.justification:
            resource_str += f"- Justification: {resource.justification}\n"
        if resource.addresses:
            resource_str += f"- Addresses: {', '.join(resource.addresses)}\n"
        if resource.phones:
            resource_str += f"- Phones: {', '.join(resource.phones)}\n"
        if resource.emails:
            resource_str += f"- Emails: {', '.join(resource.emails)}\n"
        if resource.website:
            resource_str += f"- Website: {resource.website}\n"
        formatted_resources.append(resource_str)
    return "\n".join(formatted_resources)
