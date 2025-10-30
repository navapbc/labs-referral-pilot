import logging
from pprint import pformat
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import OutputAdapter, PyPDFToDocument

from src.common import components, haystack_utils
from src.pipelines.generate_referrals.pipeline_wrapper import response_schema

logger = logging.getLogger(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals_from_document"

    def setup(self) -> None:
        pipeline = Pipeline()

        pipeline.add_component("files_to_bytestreams", components.UploadFilesToByteStreams())
        pipeline.add_component("extract_pdf_text", PyPDFToDocument())
        pipeline.add_component(
            "output_adapter",
            # https://docs.haystack.deepset.ai/docs/outputadapter
            # Use Jinja template to extract content field from documents and return as a string,
            # which is used as input to the prompt builder
            OutputAdapter(
                template="{{ documents | map(attribute='content') | list | join('\n') }}",
                output_type=str,
            ),
        )
        pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                template=haystack_utils.get_phoenix_prompt("generate_referrals"),
                required_variables=["query", "supports", "response_json"],
            ),
        )

        pipeline.add_component("load_supports", components.LoadSupports())
        pipeline.add_component("llm", components.OpenAIWebSearchGenerator())
        # For testing: pipeline.add_component("llm", components.DummyChatGenerator())

        pipeline.connect("files_to_bytestreams", "extract_pdf_text.sources")
        pipeline.connect("extract_pdf_text.documents", "output_adapter")
        pipeline.connect("output_adapter.output", "prompt_builder.query")

        pipeline.connect("load_supports.supports", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        # pipeline.draw(path="generate_referrals_from_document_pipeline.png")
        self.pipeline = pipeline

    # Called for the `{pipeline_name}/run` endpoint
    # Must use the `files` parameter name for file uploads to work
    # See https://github.com/deepset-ai/hayhooks/blob/2070f51db4c0d2bb45131b87d736304996e09058/docs/concepts/pipeline-wrapper.md#file-upload-support
    # and https://github.com/deepset-ai/hayhooks/blob/2070f51db4c0d2bb45131b87d736304996e09058/src/hayhooks/server/utils/deploy_utils.py#L287
    def run_api(self, files: Optional[List[UploadFile]] = None) -> dict:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided for processing.")

        response = self.pipeline.run(
            {
                "files_to_bytestreams": {"files": files},
                "prompt_builder": {
                    "response_json": response_schema,
                },
                "llm": {"model": "gpt-5-mini", "reasoning_effort": "low"},
            }
        )
        logger.info("Pipeline result: %s", pformat(response, width=160))
        return response
