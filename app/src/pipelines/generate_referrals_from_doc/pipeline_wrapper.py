import json
import logging
from pprint import pformat
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import OutputAdapter, PyPDFToDocument
from openinference.instrumentation import _tracers, using_metadata
from opentelemetry.trace.status import Status, StatusCode

from src.common import components, haystack_utils, phoenix_utils
from src.pipelines.generate_referrals.pipeline_wrapper import response_schema

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "generate_referrals_from_doc"

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

        pipeline.add_component("logger", components.ReadableLogger())
        pipeline.connect("llm", "logger")

        # pipeline.draw(path="generate_referrals_from_document_pipeline.png")
        self.pipeline = pipeline

    # Called for the `{pipeline_name}/run` endpoint
    # Must use the `files` parameter name for file uploads to work
    # See https://github.com/deepset-ai/hayhooks/blob/2070f51db4c0d2bb45131b87d736304996e09058/docs/concepts/pipeline-wrapper.md#file-upload-support
    # and https://github.com/deepset-ai/hayhooks/blob/2070f51db4c0d2bb45131b87d736304996e09058/src/hayhooks/server/utils/deploy_utils.py#L287
    def run_api(self, user_email: str, files: Optional[List[UploadFile]] = None) -> dict:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided for processing.")

        with using_metadata({"user_id": user_email}):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            assert isinstance(tracer, _tracers.OITracer), f"Got unexpected {type(tracer)}"
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.name, openinference_span_kind="chain"
            ) as span:
                result = self._run(files)
                span.set_input([file.filename for file in files])
                try:
                    resp_obj = json.loads(result["llm"]["replies"][-1].text)
                    span.set_output([r["name"] for r in resp_obj["resources"]])
                except (KeyError, IndexError):
                    span.set_output(result["llm"]["replies"][-1].text)
                span.set_status(Status(StatusCode.OK))
                return result

    def _run(self, files: List[UploadFile]) -> dict:
        response = self.pipeline.run(
            {
                "logger": {
                    "messages_list": [{"filenames": [file.filename for file in files]}],
                },
                "files_to_bytestreams": {"files": files},
                "prompt_builder": {
                    "response_json": response_schema,
                },
                "llm": {"model": "gpt-5-mini", "reasoning_effort": "low"},
            },
            include_outputs_from={"llm"},
        )
        logger.info("Pipeline result: %s", pformat(response, width=160))
        return response
