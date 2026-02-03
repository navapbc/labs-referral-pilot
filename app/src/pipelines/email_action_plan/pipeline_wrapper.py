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
    name = "email_action_plan"

    def setup(self) -> None:
        pipeline = Pipeline()
        pipeline.add_component("load_action_plan", components.LoadResult())
        pipeline.add_component("email_action_plan", components.EmailActionPlan())

        pipeline.connect("load_action_plan.result_json", "email_action_plan.action_plan_dict")

        pipeline.add_component("logger", components.ReadableLogger())

        self.pipeline = pipeline

    def run_api(self, action_plan_result_id: str, email: str) -> dict:
        with using_metadata({"email": email}):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            assert isinstance(tracer, _tracers.OITracer), f"Got unexpected {type(tracer)}"
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.name, openinference_span_kind="chain"
            ) as span:
                result = self._run(action_plan_result_id, email)
                span.set_input(action_plan_result_id)
                span.set_output(result["email_action_plan"]["status"])
                span.set_status(Status(StatusCode.OK))
                return result

    def _run(self, action_plan_result_id: str, email: str) -> dict:
        try:
            response = self.pipeline.run(
                {
                    "logger": {
                        "messages_list": [
                            {"action_plan_result_id": action_plan_result_id, "email": email}
                        ],
                    },
                    "load_action_plan": {
                        "result_id": action_plan_result_id,
                    },
                    "email_action_plan": {
                        "email": email,
                    },
                },
                include_outputs_from={"email_action_plan"},
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
