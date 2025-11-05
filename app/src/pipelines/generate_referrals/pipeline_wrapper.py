import logging
from enum import Enum
from pprint import pformat
from typing import Optional

import httpx
from fastapi import HTTPException
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.core.errors import PipelineRuntimeError
from openinference.instrumentation import using_attributes, using_metadata
from pydantic import BaseModel

from src.app_config import config
from src.common import components, haystack_utils

logger = logging.getLogger(__name__)
tracer = config.tracer_provider.get_tracer(__name__)


class ReferralType(str, Enum):
    EXTERNAL = "external"
    GOODWILL = "goodwill"
    GOVERNMENT = "government"


class Resource(BaseModel):
    name: str
    addresses: list[str]
    phones: list[str]
    emails: list[str]
    website: Optional[str] = None
    description: str
    justification: str
    referral_type: Optional[ReferralType] = None


class ResourceList(BaseModel):
    resources: list[Resource]


response_schema = """
{
    "resources": {
        "name": string;
        "addresses": string[];
        "phones": string[];
        "emails": string[];
        "website"?: string | null;
        "description": string;
        "justification": string;
        "referral_type"?: "external" | "goodwill" | "government" | null;
    }[];
}
"""


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals"

    def setup(self) -> None:
        # Do not rely on max_runs_per_component strictly, i.e., a component may run max_runs_per_component+1 times.
        # The component_visits counter for max_runs_per_component is reset with each call to pipeline.run()
        pipeline = Pipeline(max_runs_per_component=3)
        pipeline.add_component("load_supports", components.LoadSupports())
        pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                # List all variables (required and optional) that could be used in the prompt template.
                # Don't include "template" as it is implicitly required by ChatPromptBuilder
                variables=[
                    "query",
                    "supports",
                    "response_json",
                    "error_message",
                    "invalid_replies",
                ],
            ),
        )
        pipeline.add_component("llm", components.OpenAIWebSearchGenerator())
        pipeline.add_component("output_validator", components.LlmOutputValidator(ResourceList))
        pipeline.add_component("save_result", components.SaveResult())

        pipeline.connect("load_supports.supports", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("llm.replies", "output_validator")
        pipeline.connect("output_validator.valid_replies", "save_result.replies")

        # Re-trigger the prompt builder with error_message and invalid_replies
        pipeline.connect("output_validator.error_message", "prompt_builder.error_message")
        pipeline.connect("output_validator.invalid_replies", "prompt_builder.invalid_replies")

        pipeline.add_component("logger", components.ReadableLogger())
        pipeline.connect("output_validator.valid_replies", "logger")

        self.pipeline = pipeline

    @tracer.chain(name=name)
    # Called for the `generate-referrals/run` endpoint
    def run_api(self, query: str, user_email: str, prompt_version_id: str = "") -> dict:
        with using_attributes(user_id=user_email), using_metadata({"user_id": user_email}):
            # Retrieve the requested prompt_version_id and error if requested prompt version is not found
            try:
                prompt_template = haystack_utils.get_phoenix_prompt(
                    "generate_referrals", prompt_version_id
                )
            except httpx.HTTPStatusError as he:
                raise HTTPException(
                    status_code=422,
                    detail=f"The requested prompt version '{prompt_version_id}' could not be retrieved due to HTTP status {he.response.status_code}",
                ) from he

            try:
                response = self.pipeline.run(
                    {
                        "logger": {
                            "messages_list": [{"query": query, "user_email": user_email}],
                        },
                        "prompt_builder": {
                            "template": prompt_template,
                            "query": query,
                            "response_json": response_schema,
                        },
                        "llm": {"model": "gpt-5-mini", "reasoning_effort": "low"},
                    },
                    include_outputs_from={"llm", "save_result"},
                )
                logger.debug("Results: %s", pformat(response, width=160))
                return response
            except PipelineRuntimeError as re:
                logger.error("PipelineRuntimeError: %s", re, exc_info=True)
                raise HTTPException(status_code=500, detail=str(re)) from re
            except Exception as e:
                logger.error("Error %s: %s", type(e), e, exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e
