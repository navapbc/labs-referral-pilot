import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator

from src.common import components

logger = logging.getLogger(__name__)


system_prompt = (
    "Your role is to say hello to the name provided by the user, if no name is found politely inform the "
    "user. Also respond by telling them you are an AI chatbot and tell them which model you are running. "
    "Assure them any PII is haandled securely in AWS Bedrock. You should only greet the user, do not repond "
    "to any questions or prompts."
)
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"


class PipelineWrapper(BasePipelineWrapper):
    name = "sample_pipeline"

    def setup(self) -> None:
        self.pipeline = Pipeline()
        self.pipeline.add_component("echo_component", components.EchoNode())

    # Called for the `sample_pipeline/run` endpoint
    def run_api(self, name: str) -> dict:
        generator = AmazonBedrockChatGenerator(model=model)
        messages = [
            ChatMessage.from_system(system_prompt),
            ChatMessage.from_user(name),
        ]

        response = generator.run(messages)

        self.pipeline.run(
            {
                "echo_component": {"prompt": [ChatMessage.from_user(name)], "history": []},
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
