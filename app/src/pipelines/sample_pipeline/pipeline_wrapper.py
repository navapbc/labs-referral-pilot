import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.dataclasses.chat_message import ChatMessage

from src.common import components

logger = logging.getLogger(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "sample_pipeline"

    def setup(self) -> None:
        self.pipeline = Pipeline()
        self.pipeline.add_component("echo_component", components.EchoNode())

    # Called for the `{pipeline_name}/run` endpoint
    def run_api(self, question: str) -> dict:
        results = self.pipeline.run(
            {
                "echo_component": {"prompt": [ChatMessage.from_user(question)], "history": []},
            }
        )
        logger.info("Results: %s", pformat(results))
        return results

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
