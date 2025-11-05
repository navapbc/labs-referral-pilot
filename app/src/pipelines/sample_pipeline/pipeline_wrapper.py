import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.dataclasses.chat_message import ChatMessage
from openinference.instrumentation import using_metadata
from opentelemetry.trace.status import Status, StatusCode

from src.common import components, phoenix_utils

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)

system_msg = "This is a sample pipeline, it echoes back the system and user messages provided"


class PipelineWrapper(BasePipelineWrapper):
    name = "sample_pipeline"

    def setup(self) -> None:
        self.pipeline = Pipeline()
        self.pipeline.add_component("echo_component", components.EchoNode())
        self.pipeline.add_component("echo_component2", components.EchoNode())
        self.pipeline.add_component("logger", components.ReadableLogger())

        self.pipeline.connect("echo_component", "logger")
        self.pipeline.connect("echo_component2", "logger")

    # Called for the `sample_pipeline/run` endpoint
    def run_api(self, question: str) -> dict:
        with using_metadata({"user_id": "someone@example.com"}):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.name, openinference_span_kind="chain"
            ) as span:
                result = self._run(question)
                span.set_input(question)
                span.set_output(result["echo_component"]["full_prompt"][-1].texts)
                span.set_status(Status(StatusCode.OK))
                return result

    def _run(self, question: str) -> dict:
        messages = [
            ChatMessage.from_system(system_msg),
            ChatMessage.from_user(question),
        ]
        response = self.pipeline.run(
            {
                "logger": {
                    "messages_list": [{"question": question}],
                },
                "echo_component": {"prompt": messages, "history": []},
                "echo_component2": {"prompt": messages, "history": []},
            },
            include_outputs_from={"echo_component", "echo_component2"},
        )
        logger.info("Results: %s", pformat(response))
        return response

    # https://docs.haystack.deepset.ai/docs/hayhooks#openai-compatibility
    # Called for the `{pipeline_name}/chat`, `/chat/completions`, or `/v1/chat/completions` streaming endpoint using Server-Sent Events (SSE)
    def run_chat_completion(self, model: str, messages: list, body: dict) -> None:
        logger.info("Running chat completion with model: %s, messages: %s", model, messages)
        question = hayhooks.get_last_user_message(messages)
        logger.info("Question: %s", question)
        return hayhooks.streaming_generator(
            pipeline=self.pipeline,
            pipeline_run_args={
                "echo_component": {
                    "prompt": [ChatMessage.from_user(question)],
                    "history": messages[:-1],
                }
            },
        )
