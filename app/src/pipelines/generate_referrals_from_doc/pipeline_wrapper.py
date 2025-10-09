import json
import logging
from pprint import pformat
from typing import List, Optional

from fastapi import UploadFile
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import OutputAdapter, PyPDFToDocument
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from pydantic import BaseModel

from src.common import components, haystack_utils

logger = logging.getLogger(__name__)


class Resource(BaseModel):
    name: str
    addresses: list[str]
    phones: list[str]
    emails: list[str]
    website: str
    description: str
    justification: str


resource_as_json = json.dumps(Resource.model_json_schema(), indent=2)
model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals_from_document"

    def setup(self) -> None:
        pipeline = Pipeline()

        pipeline.add_component("files_to_bytestreams", components.UploadFilesToByteStreams())

        pipeline.add_component("converter", PyPDFToDocument())

        pipeline.add_component(
            name="output_adapter",
            # https://docs.haystack.deepset.ai/docs/outputadapter
            # Use Jinja template to extract content field from documents and return as list of strings
            # The output list[str] is used as the "supports" input to the prompt builder
            instance=OutputAdapter(
                template="{{ documents | map(attribute='content') | list }}", output_type=list[str]
            ),
        )

        prompt_template = haystack_utils.get_phoenix_prompt("generate_referrals")
        pipeline.add_component(
            instance=ChatPromptBuilder(
                template=prompt_template, required_variables=["query", "supports", "resource_json"]
            ),
            name="prompt_builder",
        )

        pipeline.add_component("llm", AmazonBedrockChatGenerator(model=model))
        # pipeline.add_component("llm", components.DummyChatGenerator())

        pipeline.connect("files_to_bytestreams", "converter.sources")
        pipeline.connect("converter.documents", "output_adapter")
        pipeline.connect("output_adapter.output", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        self.pipeline = pipeline

    # Called for the `{pipeline_name}/run` endpoint
    # Must use the `files` parameter name for file uploads to work
    # See https://github.com/deepset-ai/hayhooks/blob/2070f51db4c0d2bb45131b87d736304996e09058/docs/concepts/pipeline-wrapper.md#file-upload-support
    # and https://github.com/deepset-ai/hayhooks/blob/2070f51db4c0d2bb45131b87d736304996e09058/src/hayhooks/server/utils/deploy_utils.py#L287
    def run_api(self, query: str, files: Optional[List[UploadFile]] = None) -> dict:
        if not files:
            raise ValueError("No files provided")

        response = self.pipeline.run(
            {
                "files_to_bytestreams": {"files": files},
                "prompt_builder": {
                    "query": query,
                    "resource_json": resource_as_json,
                },
            }
        )
        logger.info("Results: %s", pformat(response, width=160))
        return response
