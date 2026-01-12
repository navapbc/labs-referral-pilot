import logging
from pprint import pformat
from typing import Generator

from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from pydantic import BaseModel

from src.app_config import config
from src.common import haystack_utils
from src.common.components import (
    LlmOutputValidator,
    OpenAIWebSearchGenerator,
    ReadableLogger,
    SaveResult,
)
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
                template=prompt_template,
                required_variables=["resources", "action_plan_json", "user_query"],
            ),
            name="prompt_builder",
        )
        pipeline.add_component("output_validator", LlmOutputValidator(ActionPlan))
        pipeline.add_component("save_result", SaveResult())

        pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("llm.replies", "output_validator")
        pipeline.connect("output_validator.valid_replies", "save_result.replies")

        pipeline.add_component("logger", ReadableLogger())
        pipeline.connect("llm", "logger")

        self.pipeline = pipeline
        self.runner = haystack_utils.TracedPipelineRunner(self.name, self.pipeline)

    # Called for the `generate-action-plan/run` endpoint
    def run_api(
        self, resources: list[Resource] | list[dict], user_email: str, user_query: str
    ) -> dict:
        resource_objects = get_resources(resources)
        pipeline_run_args = self.create_pipeline_args(
            user_email,
            resource_objects,
            user_query,
        )
        response = self.runner.return_response(
            pipeline_run_args,
            user_id=user_email,
            metadata={"user_id": user_email},
            include_outputs_from={"llm", "save_result"},
            input_=[r.name for r in resource_objects],
            extract_output=lambda response: response["llm"]["replies"][0]._content[0].text,
        )
        logger.debug("Results: %s", pformat(response, width=160))

        return {
            "response": response["llm"]["replies"][0]._content[0].text,
            "save_result": response["save_result"],
        }

    def create_pipeline_args(
        self,
        user_email: str,
        resource_objects: list[Resource],
        user_query: str,
        *,
        llm_model: str | None = None,
        reasoning_effort: str | None = None,
        streaming: bool | None = None,
    ) -> dict:
        return {
            "logger": {
                "messages_list": [
                    {"resource_count": len(resource_objects), "user_email": user_email}
                ],
            },
            "prompt_builder": {
                "resources": format_resources(resource_objects),
                "action_plan_json": action_plan_as_json,
                "user_query": user_query,
            },
            "llm": {
                "model": llm_model or config.generate_action_plan_model_version,
                "reasoning_effort": reasoning_effort or config.generate_action_plan_reasoning_level,
                "streaming": streaming or False,
            },
        }

    # https://docs.haystack.deepset.ai/docs/hayhooks#openai-compatibility
    # Called for the `{pipeline_name}/chat`, `/chat/completions`, or `/v1/chat/completions` streaming endpoint using Server-Sent Events (SSE)
    def run_chat_completion(self, model: str, messages: list, body: dict) -> Generator:
        # Note: 'model' parameter is the pipeline name, not the LLM model
        assert model == self.name, f"Unexpected model/pipeline name: {model}"

        # Extract custom parameters from the body
        resources = body.get("resources", [])
        user_email = body.get("user_email", "")
        user_query = body.get("user_query", "")

        assert resources, "resources parameter is required"
        assert user_email, "user_email parameter is required"
        assert user_query, "user_query parameter is required"

        resource_objects = get_resources(resources)
        pipeline_run_args = self.create_pipeline_args(
            user_email,
            resource_objects,
            user_query,
            llm_model=body.get("llm_model", None),
            reasoning_effort=body.get("reasoning_effort", None),
            streaming=True,
        )
        logger.info("Streaming action plan: %s", pipeline_run_args)
        return self.runner.stream_response(
            pipeline_run_args,
            user_id=user_email,
            metadata={"user_id": user_email},
            input_=[r.name for r in resource_objects],
        )


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
