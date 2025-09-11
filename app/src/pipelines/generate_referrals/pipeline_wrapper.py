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

logger = logging.getLogger(__name__)


class Resource(BaseModel):
    resource_name: str
    resource_addresses: list[str]
    resource_phones: list[str]
    description: str
    justification: str


resource_as_json = json.dumps(Resource.model_json_schema(), indent=2)

system_prompt = """
You are a supporting API for Goodwill Central Texas Referral. You are designed to help career case managers provide high-quality, local resource referrals to client's in Central Texas.
Your role is to support Goodwill Central Texas career case managers working with low-income job seekers and learners in Austin and surrounding counties (Bastrop, Blanco, Burnet, Caldwell, DeWitt, Fayette, Gillespie, Gonzales, Hays, Lavaca, Lee, Llano, Mason, Travis, Williamson).

## Task Checklist
    - Evaluate the client needs and determine their eligibility (Factors to consider: age, income, disability, immigration/veteran status, number of dependents)
    - Prioritize Goodwill resources first (Basic Needs Resource packet, Goodwill websites)
    - Rank recommendations by proximity, eligibility fit, and other relevant factors

## Core Instructions
    - Use only trusted and up-to-date sources: Goodwill, government, vetted nonprofits, trusted news outlets (Findhelp, 211, Connect ATX permitted). Never use unreliable websites (e.g., shelterlistings.org, needhelppayingbills.com).
    - Never invent or fabricate resources. If none are available, state this clearly and suggest actionable, specific next steps

    List of resources to choose from:
        {% for s in supports %}
        - {{ s.content }}
        {% endfor %}

## Response Constraints
    - Your response should ONLY include resources.
    - Do not summarize your assessment of the clients needs.
    - limit the description for a resource to be less than 255 words.
    - Return a JSON list of resources in the following format:
        '''{{ resource_json }}'''
    """
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

prompt_template = [
    ChatMessage.from_system(system_prompt),
    ChatMessage.from_user("""User query: {{ query }}"""),
]


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("llm", AmazonBedrockChatGenerator(model=model))
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
