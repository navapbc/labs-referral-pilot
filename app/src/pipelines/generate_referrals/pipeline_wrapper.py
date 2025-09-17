import json
import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from pydantic import BaseModel
from sqlalchemy.inspection import inspect

from src.app_config import config
from src.db.models.support_listing import Support
from src.common import components, haystack_utils, phoenix_utils

logger = logging.getLogger(__name__)


class Resource(BaseModel):
    resource_name: str
    resource_addresses: list[str]
    resource_phones: list[str]
    description: str
    justification: str


resource_as_json = json.dumps(Resource.model_json_schema(), indent=2)
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals"

    def setup(self) -> None:
        pipeline = Pipeline()
        # pipeline.add_component("llm", AmazonBedrockChatGenerator(model=model))
        pipeline.add_component("llm", components.EchoNode())

        prompt_ver = phoenix_utils.get_prompt_template("generate_referrals")
        prompt_template = haystack_utils.to_chat_messages(prompt_ver._template["messages"])
        pipeline.add_component(
            instance=ChatPromptBuilder(
                template=prompt_template, required_variables=["query", "supports", "resource_json"]
            ),
            name="prompt_builder",
        )
        # pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("prompt_builder", "llm.prompt")
        pipeline.connect("prompt_builder", "llm.history")

        self.pipeline = pipeline

    # Called for the `generate-referrals/run` endpoint
    def run_api(self, query: str) -> dict:
        supports_from_db = retrieve_supports_from_db()
        response = self.pipeline.run(
            {
                "prompt_builder": {
                    "query": query,
                    "supports": supports_from_db,
                    "resource_json": resource_as_json,
                },
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


def retrieve_supports_from_db() -> list[str]:
    all_supports: list[str] = []
    with config.db_session() as db_session, db_session.begin():
        all_db_supports = db_session.query(Support).all()

        for support in all_db_supports:
            support_dict = {
                c.key: getattr(support, c.key) for c in inspect(Support).mapper.column_attrs
            }
            support_as_str = json.dumps(support_dict, default=str)
            all_supports.append(support_as_str)
    return all_supports
