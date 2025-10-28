import json
import logging
from enum import Enum
from pprint import pformat
from typing import Optional

from fastapi import HTTPException
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from openinference.instrumentation import using_attributes
from pydantic import BaseModel

from src.common import components, haystack_utils

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
    referral_type: Optional[ReferralType] = None


resource_as_json = json.dumps(Resource.model_json_schema(), indent=2)
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("load_supports", components.LoadSupports())

        prompt_template = haystack_utils.get_phoenix_prompt("generate_referrals")
        pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                template=prompt_template, required_variables=["query", "supports", "resource_json"]
            ),
        )
        pipeline.add_component("llm", AmazonBedrockChatGenerator(model=model))
        pipeline.add_component("save_result", components.SaveResult())

        pipeline.connect("load_supports.supports", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("llm.replies", "save_result.replies")
        self.pipeline = pipeline

    # Called for the `generate-referrals/run` endpoint
    def run_api(
        self, query: str, user_name: str, user_email: str, prompt_version_id: str = ""
    ) -> dict:
        ctx = {
            "user_id": user_name + "%^&" + user_email
        }  # adding %^& in order to prevent MS Presidio from redacting

        with using_attributes(**ctx):
            # Retrieve the requested prompt_version_id and error if requested prompt version is not found
            try:
                prompt_template = haystack_utils.get_phoenix_prompt(
                    "generate_referrals", prompt_version_id
                )
                response = self.pipeline.run(
                    {
                        "prompt_builder": {
                            "template": prompt_template,
                            "query": query,
                            "resource_json": resource_as_json,
                        },
                    },
                    include_outputs_from={"llm", "save_result"},
                )
                logger.info("Results: %s", pformat(response, width=160))
                return response
            except Exception as e:
                logger.error("The requested prompt version could not be retrieved")
                raise HTTPException(
                    status_code=400,
                    detail=f"The requested prompt version '{prompt_version_id}' could not be retrieved",
                ) from e
