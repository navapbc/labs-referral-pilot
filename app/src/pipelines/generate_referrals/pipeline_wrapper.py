import json
import logging
from enum import Enum
from pprint import pformat
from typing import Optional
from uuid import UUID

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from pydantic import BaseModel

from src.app_config import config
from src.common import haystack_utils
from src.db.models.support_listing import Support

logger = logging.getLogger(__name__)

class ReferralType(str, Enum):
    EXTERNAL = "external"
    GOODWILL = "goodwill"
    GOVERNMENT = "government"

class Resource(BaseModel):
    name: str
    addresses: list[str]
    phones: list[str]
    emails: list[str]
    website: str
    description: str
    justification: str
    referral_type: Optional[ReferralType]


resource_as_json = json.dumps(Resource.model_json_schema(), indent=2)
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("llm", AmazonBedrockChatGenerator(model=model))

        prompt_template = haystack_utils.get_phoenix_prompt("generate_referrals")
        pipeline.add_component(
            instance=ChatPromptBuilder(
                template=prompt_template, required_variables=["query", "supports", "resource_json"]
            ),
            name="prompt_builder",
        )
        pipeline.connect("prompt_builder", "llm.messages")

        self.pipeline = pipeline

    # Called for the `generate-referrals/run` endpoint
    def run_api(self, query: str) -> dict:
        supports_from_db = format_support_strings()
        response = self.pipeline.run(
            {
                "prompt_builder": {
                    "query": query,
                    "supports": supports_from_db.values(),
                    "resource_json": resource_as_json,
                },
            }
        )
        logger.info("Results: %s", pformat(response, width=160))
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


def format_support_strings() -> dict[UUID, str]:
    with config.db_session() as db_session, db_session.begin():
        return {
            support.id: (
                f"Name: {support.name}\n"
                f"- Description: {support.description}\n"
                f"- Addresses: {', '.join(support.addresses)}\n"
                f"- Phones: {', '.join(support.phone_numbers)}\n"
                f"- Website: {support.website}\n"
                f"- Email Addresses: {', '.join(support.email_addresses)}\n"
            )
            for support in db_session.query(Support).all()
        }
