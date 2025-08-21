import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
logger = logging.getLogger(__name__)
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator

from src.common import components, phoenix_utils

logger = logging.getLogger(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "sample_pipeline"

    def setup(self) -> None:
        self.pipeline = Pipeline()
        self.pipeline.add_component("echo_component", components.EchoNode())

    # Called for the `{pipeline_name}/run` endpoint
    def run_api(self, question: str) -> dict:

        generator = AmazonBedrockChatGenerator(model="us.anthropic.claude-3-5-sonnet-20241022-v2:0")
        messages = [ChatMessage.from_system("Your role is to say hello to the name provided in the question, if no name is found politely inform the user that no name was provided"),
                    ChatMessage.from_user(question)]

        response = generator.run(messages)

        results = self.pipeline.run(
            {
                "echo_component": {"prompt": [ChatMessage.from_user(question)], "history": []},
            }
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
