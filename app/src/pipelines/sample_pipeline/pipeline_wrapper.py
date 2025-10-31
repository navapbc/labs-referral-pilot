import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.dataclasses.chat_message import ChatMessage

from src.common import components

logger = logging.getLogger(__name__)


system_msg = "This is a sample pipeline, it echoes back the system and user messages provided"


from openinference.instrumentation import capture_span_context
from phoenix.client import Client

client = Client()

class PipelineWrapper(BasePipelineWrapper):
    name = "sample_pipeline"

    def setup(self) -> None:
        self.pipeline = Pipeline()
        self.pipeline.add_component("echo_component", components.EchoNode())

    # Called for the `sample_pipeline/run` endpoint
    def run_api(self, question: str) -> dict:
        messages = [
            ChatMessage.from_system(system_msg),
            ChatMessage.from_user(question),
        ]
        with capture_span_context() as capture:
            response = self.pipeline.run(
                {
                    "echo_component": {"prompt": messages, "history": []},
                }
            )
            logger.info("Results: %s", pformat(response))

            first_span_id = capture.get_first_span_id()
            if first_span_id:
                # Apply user feedback to the first span
                client.spans.add_span_annotation(
                    span_id=first_span_id,
                    annotation_name="user_info",
                    annotator_kind="CODE",
                    label="my_label",
                    score=1.0,
                    explanation="my_explanation",
                    metadata={"question": question},
                    identifier="my_identifier",
                )
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
