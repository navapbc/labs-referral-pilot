# TODO: remove
import json
import logging
import uuid
from enum import Enum
from pprint import pformat
from typing import Generator, Optional

import httpx
from fastapi import HTTPException
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from pydantic import BaseModel

from src.app_config import config
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
        self.pipeline = self._create_pipeline()
        self.runner = haystack_utils.TracedPipelineRunner(self.name, self.pipeline)

    def _create_pipeline(self) -> Pipeline:
        # Do not rely on max_runs_per_component strictly, i.e., a component may run max_runs_per_component+1 times.
        # The component_visits counter for max_runs_per_component is reset with each call to pipeline.run()
        pipeline = Pipeline(max_runs_per_component=3)
        # pipeline.add_component("load_supports", components.LoadSupports())
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
        return pipeline

    # Called for the `generate-referrals/run` endpoint
    def run_api(
        self, query: str, user_email: str, prompt_version_id: str = "", suffix: str = ""
    ) -> dict:
        # Retrieve the requested prompt (with optional prompt_version_id and/or suffix)

        pipeline_run_args = self.create_pipeline_args(
            query,
            user_email,
            prompt_version_id=prompt_version_id,
            suffix=suffix,
            region=suffix or "centraltx",
        )

        def extract_output(result: dict) -> list | str:
            try:
                resp_obj = json.loads(result["llm"]["replies"][-1].text)
                return [r["name"] for r in resp_obj["resources"]]
            except (KeyError, IndexError):
                return result["llm"]["replies"][-1].text

        response = self.runner.return_response(
            pipeline_run_args,
            user_id=user_email,
            metadata={"user_id": user_email},
            include_outputs_from={"llm", "save_result"},
            input_=query,
            extract_output=extract_output,
            parent_span_name_suffix=suffix,
        )
        logger.debug("Results: %s", pformat(response, width=160))
        return response

    def create_pipeline_args(
        self,
        query: str,
        user_email: str,
        *,
        region: str,
        prompt_version_id: str = "",
        suffix: str = "",
        llm_model: str | None = None,
        reasoning_effort: str | None = None,
        streaming: bool = False,
    ) -> dict:
        """Create pipeline run arguments with optional overrides for model, reasoning effort, and streaming."""
        try:
            prompt_template = haystack_utils.get_phoenix_prompt(
                "generate_referrals", prompt_version_id=prompt_version_id, suffix=suffix
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=422,
                detail=f"The requested prompt version '{prompt_version_id}' with suffix '{suffix}' could not be retrieved",
            ) from e

        return {
            "logger": {
                "messages_list": [{"query": query, "user_email": user_email}],
            },
            "prompt_builder": {
                "template": prompt_template,
                "query": query,
                "response_json": response_schema,
            },
            "llm": {
                "model": llm_model or config.generate_referrals_model_version,
                "reasoning_effort": reasoning_effort or config.generate_referrals_reasoning_level,
                "streaming": streaming,
            },
        }

    # https://docs.haystack.deepset.ai/docs/hayhooks#openai-compatibility
    # Called for the `{pipeline_name}/chat`, `/chat/completions`, or `/v1/chat/completions` streaming endpoint using Server-Sent Events (SSE)
    def run_chat_completion(self, model: str, messages: list, body: dict) -> Generator:
        # Note: 'model' parameter is the pipeline name, not the LLM model
        assert model == self.name, f"Unexpected model/pipeline name: {model}"

        # Extract custom parameters from the body
        query = body.get("query", "")
        user_email = body.get("user_email", "")
        suffix = body.get("suffix", "")

        if not query:
            raise ValueError("query parameter is required")

        if not user_email:
            raise ValueError("user_email parameter is required")

        pipeline_run_args = self.create_pipeline_args(
            query,
            user_email,
            prompt_version_id=body.get("prompt_version_id", ""),
            suffix=body.get("suffix", ""),
            region=suffix or "centraltx",
            llm_model=body.get("llm_model", None),
            reasoning_effort=body.get("reasoning_effort", None),
            streaming=True,
        )

        # Generate result_id upfront to pass to both SaveResult and the hook
        result_id = str(uuid.uuid4())
        pipeline_run_args["save_result"] = {"result_id": result_id}

        logger.info("Streaming referrals: %s", pipeline_run_args)
        return self.runner.stream_response(
            pipeline_run_args,
            user_id=user_email,
            metadata={"user_id": user_email},
            input_=[query],
            generator_hook=haystack_utils.create_result_id_hook(self.pipeline, result_id),
        )
