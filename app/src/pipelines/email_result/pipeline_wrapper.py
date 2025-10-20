import logging
from pprint import pformat

from fastapi import HTTPException
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.core.errors import PipelineRuntimeError

from src.common import components

logger = logging.getLogger(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "email_result"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("load_result", components.LoadResult())
        pipeline.add_component("email_result", components.EmailResult())

        pipeline.connect("load_result.result_json", "email_result.json_dict")
        self.pipeline = pipeline

    def run_api(self, result_id: str, email: str) -> dict:
        try:
            response = self.pipeline.run(
                {
                    "load_result": {
                        "result_id": result_id,
                    },
                    "email_result": {
                        "email": email,
                    },
                },
            )
            logger.info("Results: %s", pformat(response, width=160))
            return response
        except PipelineRuntimeError as re:
            error_msg = str(re)
            if "No result found with id=" in error_msg:
                status_code = 400  # User error
            else:
                status_code = 500  # Internal error

            raise HTTPException(
                status_code=status_code,
                detail=f"Error occurred: {error_msg}",
            ) from re
