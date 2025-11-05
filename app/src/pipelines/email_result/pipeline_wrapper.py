import logging
from pprint import pformat

from fastapi import HTTPException
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.core.errors import PipelineRuntimeError
from openinference.instrumentation import using_metadata

from src.common import components, phoenix_utils

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "email_result"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("load_result", components.LoadResult())
        pipeline.add_component("email_result", components.EmailResult())

        pipeline.connect("load_result.result_json", "email_result.json_dict")

        pipeline.add_component("logger", components.ReadableLogger())

        self.pipeline = pipeline

    @tracer.chain(name=name)
    def run_api(self, result_id: str, email: str) -> dict:
        with using_metadata({"email": email}):
            try:
                response = self.pipeline.run(
                    {
                        "logger": {
                            "messages_list": [{"result_id": result_id, "email": email}],
                        },
                        "load_result": {
                            "result_id": result_id,
                        },
                        "email_result": {
                            "email": email,
                        },
                    },
                    include_outputs_from={"email_result"},
                )
                logger.debug("Results: %s", pformat(response, width=160))
                return response
            except PipelineRuntimeError as re:
                error_msg = str(re)
                if re.component_type == components.LoadResult:
                    if "Invalid JSON format in result" in error_msg:
                        status_code = 500  # Internal error
                    else:
                        status_code = 400  # User error
                else:
                    status_code = 500  # Internal error

                raise HTTPException(
                    status_code=status_code,
                    detail=f"Error occurred: {error_msg}",
                ) from re
