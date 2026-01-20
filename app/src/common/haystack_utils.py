import logging
import uuid
from typing import Any, Callable, Generator, Sequence

import hayhooks
from fastapi import HTTPException
from haystack import Pipeline
from haystack.core.errors import PipelineRuntimeError
from haystack.dataclasses.chat_message import ChatMessage
from haystack.dataclasses.streaming_chunk import StreamingChunk
from openinference.instrumentation import using_attributes
from opentelemetry.trace import Span
from opentelemetry.trace.status import Status, StatusCode
from phoenix.client.__generated__ import v1

from src.common import phoenix_utils
from src.common.components import SaveResult


def get_phoenix_prompt(
    prompt_name: str, prompt_version_id: str = "", suffix: str = ""
) -> list[ChatMessage]:
    full_prompt_name = f"{prompt_name}_{suffix}" if suffix else prompt_name
    prompt_ver = phoenix_utils.get_prompt_template(full_prompt_name, prompt_version_id)
    return to_chat_messages(prompt_ver._template["messages"])


def to_chat_messages(
    msg_list: Sequence[str | dict | v1.PromptMessage | ChatMessage],
) -> list[ChatMessage]:
    """Convert a list of dicts or Phoenix PromptMessage to a list of Haystack ChatMessage."""
    messages = []
    for msg in msg_list:
        if isinstance(msg, ChatMessage):
            messages.append(msg)
            continue
        elif not isinstance(msg, dict):  # PromptMessage is a TypedDict
            raise ValueError(f"Expected dict or ChatMessage, got {type(msg)}")

        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            assert (
                len(content) == 1
            ), f"Expected single content, got {len(content)} items: {content}"
            assert content[0]["type"] == "text", f"Expected text content, got {content[0]['type']}"
            assert "text" in content[0], f"Expected 'text' in content[0], got {content[0]}"
            text = content[0]["text"]
        else:
            raise ValueError(f"Unexpected content type: {type(content)} for message {msg}")

        if role == "system":
            assert isinstance(text, str), f"Expected string, got {type(text)}"
            chat_msg = ChatMessage.from_system(text)
        elif role == "user":
            assert isinstance(text, str), f"Expected string, got {type(text)}"
            chat_msg = ChatMessage.from_user(text)
        elif role == "assistant":
            assert isinstance(text, str), f"Expected string, got {type(text)}"
            chat_msg = ChatMessage.from_assistant(text)
        else:
            raise ValueError(f"Unexpected role: {role} for message {msg}")
        messages.append(chat_msg)

    return messages


def create_result_id_hook(pipeline: Pipeline) -> Callable[[dict], Generator]:
    """Creates a pregenerator hook that generates result_id and yields it as first chunk.

    This hook is specific to pipelines that use the SaveResult component and need to
    return the result_id to the frontend for caching/reference.

    Args:
        pipeline: The Haystack pipeline to check for SaveResult component

    Raises:
        ValueError: If the pipeline does not have a SaveResult component
    """
    # Find the SaveResult component name in the pipeline
    # NOTE: pipeline.walk() Visits each component in the pipeline exactly once and yields its name and instance.
    # https://docs.haystack.deepset.ai/reference/pipeline-api#asyncpipelinewalk
    save_result_component_name = next(
        (name for name, comp in pipeline.walk() if isinstance(comp, SaveResult)),
        None,
    )

    if save_result_component_name is None:
        raise ValueError(
            "create_result_id_hook requires a pipeline with a SaveResult component. "
            "Do not use this hook for pipelines without SaveResult."
        )

    def hook(pipeline_run_args: dict) -> Generator:
        result_id = str(uuid.uuid4())

        # Add to pipeline args for SaveResult component
        if save_result_component_name not in pipeline_run_args:  # checking to prevent KeyError
            pipeline_run_args[save_result_component_name] = {}
        pipeline_run_args[save_result_component_name]["result_id"] = result_id

        # Yield as first chunk for frontend
        yield StreamingChunk(content=f'{{"result_id": "{result_id}"}}\n')

    return hook


logger = logging.getLogger(__name__)


class TracedPipelineRunner:
    """Helper class to run Haystack pipelines with OpenInference tracing."""

    def __init__(self, parent_span_name: str, pipeline: Pipeline) -> None:
        self.parent_span_name = parent_span_name
        self.pipeline = pipeline

    def stream_response(
        self,
        pipeline_run_args: dict,
        *,
        user_id: str,
        metadata: dict[str, Any],
        input_: Any | None = None,
        shorten_output: Callable[[str], str] = lambda resp: resp,
        parent_span_name_suffix: str | None = None,
        pregenerator_hook: Callable[[dict], Generator] | None = None,
    ) -> Generator:
        # Must set using attributes and metadata tracer context before calling tracer.start_as_current_span()
        with using_attributes(user_id=user_id, metadata=metadata):
            with phoenix_utils.tracer().start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                f"{self.parent_span_name}--{parent_span_name_suffix}"
                if parent_span_name_suffix
                else self.parent_span_name,
                openinference_span_kind="chain",
            ) as span:
                assert isinstance(span, Span), f"Got unexpected {type(span)}"
                try:
                    span.set_input(input_)

                    # Call pregenerator_hook if provided (inside span, before streaming)
                    if pregenerator_hook:
                        for chunk in pregenerator_hook(pipeline_run_args):
                            yield chunk

                    # hayhooks.streaming_generator() creates a thread that now inherits OpenTelemetry context
                    # thanks to ThreadingInstrumentor enabled in phoenix_utils.py
                    # streaming_generator() must be run inside the span context to inherit correctly
                    generator = hayhooks.streaming_generator(
                        pipeline=self.pipeline,
                        pipeline_run_args=pipeline_run_args,
                    )

                    # Stream chunks with each 'yield' call
                    chunk_count = 0
                    full_response = []
                    for chunk in generator:
                        chunk_count += 1
                        if hasattr(chunk, "content"):
                            full_response.append(chunk.content)
                        # Must yield chunks one by one for SSE
                        # Must yield in the tracer span context to have spans linked as child spans
                        yield chunk

                    logger.info("Successfully streamed %d chunks", chunk_count)
                    response_text = "".join(full_response) if full_response else ""
                    span.set_output(shorten_output(response_text))
                    span.set_status(Status(StatusCode.OK))
                except PipelineRuntimeError as e:
                    logger.error("PipelineRuntimeError: %s", e, exc_info=True)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise HTTPException(status_code=500, detail=str(e)) from e
                except Exception as e:
                    logger.error("Error during streaming: %s", e, exc_info=True)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise HTTPException(status_code=500, detail=str(e)) from e

    def return_response(
        self,
        pipeline_run_args: dict,
        *,
        user_id: str,
        metadata: dict[str, Any],
        input_: Any | None = None,
        include_outputs_from: set[str] | None = None,
        extract_output: Callable[[dict], Any] = lambda resp: resp,
        parent_span_name_suffix: str | None = None,
    ) -> dict:
        # Must set using_metadata context before calling tracer.start_as_current_span()
        with using_attributes(user_id=user_id, metadata=metadata):
            with phoenix_utils.tracer().start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                f"{self.parent_span_name}--{parent_span_name_suffix}"
                if parent_span_name_suffix
                else self.parent_span_name,
                openinference_span_kind="chain",
            ) as span:
                try:
                    result = self.pipeline.run(
                        pipeline_run_args,
                        include_outputs_from=include_outputs_from,
                    )
                    # Shorter than span.set_attribute(SpanAttributes.INPUT_VALUE, ...)
                    span.set_input(input_)
                    span.set_output(extract_output(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except PipelineRuntimeError as e:
                    logger.error("PipelineRuntimeError: %s", e, exc_info=True)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise HTTPException(status_code=500, detail=str(e)) from e
                except Exception as e:
                    logger.error("Error during pipeline run: %s", e, exc_info=True)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e
