"""
Email Responses Pipeline Wrapper

Consolidated pipeline for emailing resources, action plans, or both to users.

This pipeline replaces three previous separate pipelines:
- email_result (resources only)
- email_action_plan (action plan only)
- email_full_result (both resources and action plan)

The pipeline dynamically handles all three scenarios based on which result IDs are provided.

API Parameters:
    email (str): Recipient email address (required)
    resources_result_id (str, optional): ID of resources result to load and email
    action_plan_result_id (str, optional): ID of action plan result to load and email

At least one result_id must be provided.

Examples:
    # Email only resources
    POST /email_responses
    {
        "email": "user@example.com",
        "resources_result_id": "abc123"
    }

    # Email only action plan
    POST /email_responses
    {
        "email": "user@example.com",
        "action_plan_result_id": "xyz789"
    }

    # Email both resources and action plan
    POST /email_responses
    {
        "email": "user@example.com",
        "resources_result_id": "abc123",
        "action_plan_result_id": "xyz789"
    }
"""

import logging
from pprint import pformat
from typing import Optional

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
    """
    Unified email pipeline that handles sending resources, action plans, or both.

    This wrapper consolidates three previous pipelines into one, reducing code
    duplication and simplifying maintenance. The pipeline dynamically loads and
    emails content based on which result IDs are provided.
    """

    name = "email_responses"

    def setup(self) -> None:
        """
        Configure the pipeline with components for loading results and sending emails.

        Pipeline structure:
            load_resources (optional) ──┐
                                         ├──> email_responses
            load_action_plan (optional) ─┘

        Both loaders use LoadResultOptional which gracefully handles None/empty IDs.
        The email_responses component formats and sends email based on what's loaded.
        """
        pipeline = Pipeline()

        # Add optional loaders for resources and action plan
        pipeline.add_component("load_resources", components.LoadResultOptional())
        pipeline.add_component("load_action_plan", components.LoadResultOptional())

        # Add unified email component that handles all scenarios
        pipeline.add_component("email_responses", components.EmailResponses())

        # Connect loaders to email component
        pipeline.connect("load_resources.result_json", "email_responses.resources_dict")
        pipeline.connect("load_action_plan.result_json", "email_responses.action_plan_dict")

        # Add logger for debugging
        pipeline.add_component("logger", components.ReadableLogger())

        self.pipeline = pipeline

    def run_api(
        self,
        email: str,
        resources_result_id: Optional[str] = None,
        action_plan_result_id: Optional[str] = None,
    ) -> dict:
        """
        Send an email with resources, action plan, or both based on provided result IDs.

        Args:
            email: Recipient email address (required)
            resources_result_id: ID of resources result to load (optional)
            action_plan_result_id: ID of action plan result to load (optional)

        Returns:
            dict: Pipeline response containing status, email, and message

        Raises:
            HTTPException: If neither result_id is provided or if pipeline execution fails
        """
        # Validate that at least one result_id is provided
        if not resources_result_id and not action_plan_result_id:
            raise HTTPException(
                status_code=400,
                detail="At least one of resources_result_id or action_plan_result_id must be provided",
            )

        with using_metadata({"email": email}):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            assert isinstance(tracer, _tracers.OITracer), f"Got unexpected {type(tracer)}"
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.name, openinference_span_kind="chain"
            ) as span:
                result = self._run(resources_result_id, action_plan_result_id, email)
                span.set_input(
                    {
                        "resources_result_id": resources_result_id,
                        "action_plan_result_id": action_plan_result_id,
                        "email": email,
                    }
                )
                span.set_output(result["email_responses"]["status"])
                span.set_status(Status(StatusCode.OK))
                return result

    def _run(
        self,
        resources_result_id: Optional[str],
        action_plan_result_id: Optional[str],
        email: str,
    ) -> dict:
        """
        Internal method to execute the pipeline.

        Args:
            resources_result_id: ID of resources result to load (optional)
            action_plan_result_id: ID of action plan result to load (optional)
            email: Recipient email address

        Returns:
            dict: Pipeline execution results

        Raises:
            HTTPException: If pipeline execution fails with appropriate status code
        """
        try:
            # Build run data with optional result IDs
            # LoadResultOptional will handle None values gracefully
            run_data = {
                "logger": {
                    "messages_list": [
                        {
                            "resources_result_id": resources_result_id or "none",
                            "action_plan_result_id": action_plan_result_id or "none",
                            "email": email,
                        }
                    ],
                },
                "load_resources": {
                    "result_id": resources_result_id,
                },
                "load_action_plan": {
                    "result_id": action_plan_result_id,
                },
                "email_responses": {
                    "email": email,
                },
            }

            response = self.pipeline.run(
                run_data,
                include_outputs_from={"email_responses"},
            )
            logger.debug("Results: %s", pformat(response, width=160))
            return response

        except PipelineRuntimeError as re:
            # Handle pipeline errors with appropriate status codes
            error_msg = str(re)

            # Determine if this is a user error (bad input) or server error
            if re.component_type == components.LoadResultOptional:
                if "Invalid JSON format in result" in error_msg:
                    status_code = 500  # Internal error - bad data in database
                elif "No result found" in error_msg:
                    status_code = 400  # User error - invalid result_id
                else:
                    status_code = 400  # User error - likely bad result_id
            else:
                status_code = 500  # Internal error - email sending or other component failure

            raise HTTPException(
                status_code=status_code,
                detail=f"Error occurred: {error_msg}",
            ) from re
