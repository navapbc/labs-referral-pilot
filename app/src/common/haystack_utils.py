import logging
from typing import Any, Callable, Generator, Sequence

import hayhooks
from haystack import Pipeline
from haystack.dataclasses.chat_message import ChatMessage
from openinference.instrumentation import using_metadata
from opentelemetry.trace.status import Status, StatusCode
from phoenix.client.__generated__ import v1

from src.common import phoenix_utils


def get_phoenix_prompt(prompt_name: str, prompt_version_id: str = "") -> list[ChatMessage]:
    prompt_ver = phoenix_utils.get_prompt_template(prompt_name, prompt_version_id)
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


logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class TracedPipelineRunner:
    """Helper class to run Haystack pipelines with OpenInference tracing."""

    def __init__(self, parent_span_name: str, pipeline: Pipeline) -> None:
        self.parent_span_name = parent_span_name
        self.pipeline = pipeline

    def stream_response(
        self,
        pipeline_run_args: dict,
        *,
        metadata: dict[str, Any],
        input_: Any | None = None,
        extract_output: Callable[[str], str] = lambda resp: resp,
    ) -> Generator:
        with using_metadata(metadata):
            # Must set using_metadata context before calling tracer.start_as_current_span()
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.parent_span_name, openinference_span_kind="chain"
            ) as span:
                try:
                    span.set_input(input_)

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
                    span.set_output(extract_output(response_text))
                    span.set_status(Status(StatusCode.OK))
                except Exception as e:
                    logger.error("Error during streaming: %s", e, exc_info=True)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

    def return_response(
        self,
        pipeline_run_args: dict,
        *,
        metadata: dict[str, Any],
        input_: Any | None = None,
        include_outputs_from: set[str] | None = None,
        extract_output: Callable[[str], str] = lambda resp: resp,
    ) -> dict:
        # Must set using_metadata context before calling tracer.start_as_current_span()
        with using_metadata(metadata):
            with tracer.start_as_current_span(  # pylint: disable=not-context-manager,unexpected-keyword-arg
                self.parent_span_name, openinference_span_kind="chain"
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
                except Exception as e:
                    logger.error("Error during pipeline run: %s", e, exc_info=True)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
