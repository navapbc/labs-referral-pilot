import logging
from pprint import pformat

from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from openinference.instrumentation import _tracers, using_attributes, using_metadata
from opentelemetry.trace.status import Status, StatusCode
from pydantic import BaseModel

from src.common import haystack_utils, phoenix_utils
from src.common.components import (
    LlmOutputValidator,
    OpenAIWebSearchGenerator,
    ReadableLogger,
    SaveResult,
)
from src.pipelines.generate_referrals.pipeline_wrapper import Resource

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


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

    # Called for the `generate-action-plan/run` endpoint
    def run_api(
        self, resources: list[Resource] | list[dict], user_email: str, user_query: str
    ) -> dict:
        resource_objects = get_resources(resources)

        with using_attributes(user_id=user_email), using_metadata({"user_id": user_email}):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            assert isinstance(tracer, _tracers.OITracer), f"Got unexpected {type(tracer)}"
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.name, openinference_span_kind="chain"
            ) as span:
                result = self._run(resource_objects, user_email, user_query)
                span.set_input([r.name for r in resource_objects])
                span.set_output(result["response"])
                span.set_status(Status(StatusCode.OK))
                return result

    def _run(self, resource_objects: list[Resource], user_email: str, user_query: str) -> dict:
        response = self.pipeline.run(
            {
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
                "llm": {"model": "gpt-5-mini", "reasoning_effort": "low"},
            },
            include_outputs_from={"llm"},
        )
        logger.debug("Results: %s", pformat(response, width=160))
        return {"response": response["llm"]["replies"][0]._content[0].text}


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
