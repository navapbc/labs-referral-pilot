import logging
from pprint import pformat

from fastapi import HTTPException
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.core.errors import PipelineRuntimeError
from openinference.instrumentation import _tracers, using_metadata
from opentelemetry.trace.status import Status, StatusCode

from src.common import components, phoenix_utils

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class PipelineWrapper(BasePipelineWrapper):
    name = "email_result"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("load_resources", components.LoadResult())
        pipeline.add_component("load_action_plan", components.LoadResult())
        pipeline.add_component("email_result", components.EmailFullResult())

        pipeline.connect("load_resources.result_json", "email_result.resources_dict")
        pipeline.connect("load_action_plan.result_json", "email_result.action_plan_dict")
        pipeline.add_component("logger", components.ReadableLogger())

        self.pipeline = pipeline

    def run_api(self, resources_result_id: str, action_plan_results_id: str, email: str) -> dict:
        with using_metadata({"email": email}):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            assert isinstance(tracer, _tracers.OITracer), f"Got unexpected {type(tracer)}"
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.name, openinference_span_kind="chain"
            ) as span:
                result = self._run(resources_result_id, action_plan_results_id, email)
                span.set_input(
                    {
                        "resources_result_id": resources_result_id,
                        "action_plan_results_id": action_plan_results_id,
                    }
                )
                span.set_output(result["email_result"]["status"])
                span.set_status(Status(StatusCode.OK))
                return result

    def _run(self, resources_result_id: str, action_plan_results_id: str, email: str) -> dict:
        try:
            run_data = {
                "logger": {
                    "messages_list": [
                        {
                            "resources_result_id": resources_result_id,
                            "action_plan_results_id": action_plan_results_id,
                            "email": email,
                        }
                    ],
                },
                "load_resources": {
                    "result_id": resources_result_id,
                },
                "email_result": {
                    "email": email,
                },
            }

            run_data["load_action_plan"] = {
                "result_id": action_plan_results_id,
            }

            response = self.pipeline.run(
                run_data,
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
