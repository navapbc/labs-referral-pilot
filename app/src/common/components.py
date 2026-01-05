"""
Components cannot be defined in pipelines themselves, so define them here.

The following applies to Pipeline, as well as AsyncPipeline.

When a Hayhooks API endpoint is called by a client, different threads are used
to handle the requests, but the same PipelineWrapper instance is used by the threads!
This means that pipeline component instances are used by different threads,
so the components must be thread-safe.
"""

import json
import logging
from json import JSONDecodeError
from pprint import pformat
from typing import Any, Callable, List, Optional, TypeVar

from fastapi import UploadFile
from haystack import component
from haystack.core.component.types import Variadic
from haystack.dataclasses.byte_stream import ByteStream
from haystack.dataclasses.chat_message import ChatMessage
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from src.app_config import config
from src.common.send_email import send_email
from src.db.models.support_listing import LlmResponse, Support

logger = logging.getLogger(__name__)


def format_resources(resources: list[dict]) -> str:
    return "\n\n".join([format_resource(resource) for resource in resources])


def format_resource(resource: dict) -> str:
    return "\n".join(
        [
            f"### {resource.get('name', 'Unnamed Resource')}",
            f"- Referral Type: {resource.get('referral_type', 'None')}",
            f"- Description: {resource.get('description', 'None')}",
            f"- Website: {resource.get('website', 'None')}",
            f"- Phone: {', '.join(resource.get('phones', ['None']))}",
            f"- Email: {', '.join(resource.get('emails', ['None']))}",
            f"- Addresses: {', '.join(resource.get('addresses', ['None']))}",
        ]
    )


def format_action_plan(action_plan: dict) -> str:
    """Format the action plan for email display. Returns empty string if no action plan."""
    if not action_plan:
        return ""

    title = action_plan.get("title", "Your Action Plan")
    summary = action_plan.get("summary", "")
    content = action_plan.get("content", "")

    parts = [f"## {title}"]
    if summary:
        parts.append(f"\n{summary}")
    if content:
        parts.append(f"\n{content}")

    return "\n".join(parts)


@component
class EchoNode:
    """
    A custom node/component that simply echoes the input messages.
    Useful for testing, debugging, or as a placeholder in pipelines.
    """

    @component.output_types(full_prompt=List[ChatMessage])
    def run(self, prompt: List[ChatMessage], history: List[ChatMessage]) -> dict:
        full_prompt = history + prompt
        logger.info("Full prompt: %s", pformat(full_prompt))
        return {"full_prompt": full_prompt}


@component
class UploadFilesToByteStreams:
    """Converts list of UploadFile to list of ByteStream"""

    @component.output_types(byte_streams=List[ByteStream])
    def run(self, files: List[UploadFile]) -> dict:
        return {
            "byte_streams": [
                ByteStream.from_dict(
                    {
                        "data": f.file.read(),
                        "meta": {"filename": f.filename, "size": f.size},
                        "mime_type": f.content_type,
                    }
                )
                for f in files
            ]
        }


@component
class LoadSupports:
    """Loads support listings from the database and returns them as formatted strings."""

    @component.output_types(supports=list[str])
    def run(self) -> dict:
        with config.db_session() as db_session, db_session.begin():
            supports = [
                (
                    f"Name: {support.name}\n"
                    f"- Description: {support.description}\n"
                    f"- Addresses: {', '.join(support.addresses)}\n"
                    f"- Phones: {', '.join(support.phone_numbers)}\n"
                    f"- Website: {support.website}\n"
                    f"- Email Addresses: {', '.join(support.email_addresses)}\n"
                )
                for support in db_session.query(Support).all()
            ]
            return {"supports": supports}


@component
class SaveResult:
    """Saves LLM response to the database."""

    @component.output_types(result_id=str)
    def run(self, replies: List[ChatMessage]) -> dict:
        logger.info("Saving LLM result to database: %r", pformat(replies, width=160))
        assert replies, "Expected at least one reply"
        text_result = replies[0].text
        with config.db_session() as db_session, db_session.begin():
            llm_result = LlmResponse(raw_text=text_result)
            db_session.add(llm_result)
            db_session.flush()  # To get the id assigned
            result_id = str(llm_result.id)
            logger.info("Saved LLM result with id=%s", result_id)
            return {"result_id": result_id}


@component
class DummyChatGenerator:
    """
    A dummy chat generator that echoes back the messages used only for development.
    Temporarily replace AmazonBedrockChatGenerator with this to avoid incurring LLM costs.
    """

    @component.output_types(replies=List[ChatMessage])
    def run(self, messages: List[ChatMessage]) -> dict:
        replies = messages
        logger.info("replies: %s", pformat(replies))
        reply = [f"## {msg.role} said: {msg.text[:200] if msg.text else " "}..." for msg in replies]
        return {"replies": [ChatMessage.from_assistant("\n\n".join(reply))]}


@component
class LoadResult:
    """
    Loads result from database.
    """

    @component.output_types(result_json=dict)
    def run(self, result_id: str) -> dict:
        with config.db_session() as db_session, db_session.begin():
            db_record = (
                db_session.query(LlmResponse).filter(LlmResponse.id == result_id).one_or_none()
            )

            if not db_record:
                raise ValueError(f"No result found with id={result_id}")

            logger.info("Loaded LlmResponse:\n%s", db_record.raw_text)
            text = db_record.raw_text

        # Extract JSON object from raw_text string by searching for the first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Invalid JSON format in result with id={result_id}: {text!r}")

        json_dict = json.loads(text[start : end + 1])
        return {"result_json": json_dict}


@component
class OpenAIWebSearchGenerator:
    """Searches the web using OpenAI's web search capabilities and generates a response."""

    @component.output_types(replies=List[ChatMessage])
    def run(
        self,
        messages: list[ChatMessage],
        domain: str | None = None,
        model: str = config.default_openai_model_version,
        reasoning_effort: str = config.default_openai_reasoning_level,
    ) -> dict:
        """
        Run the OpenAI web search generator.

        Args:
            messages: List of ChatMessage objects to send to the API
            domain: Domain to restrict web search to

        Returns:
            Dictionary with response key containing string of response
        """

        logger.info(
            "Calling OpenAI API with web_search, model=%s, domain=%s, reasoning_effort=%s",
            model,
            domain,
            reasoning_effort,
        )

        assert len(messages) == 1
        prompt = messages[0].text
        logger.debug("Prompt: %s", pformat(prompt, width=160))

        api_params: dict = {
            "model": model,
            "input": prompt,
            "reasoning": {"effort": reasoning_effort},
            "tools": [{"type": "web_search"}],
        }

        if domain:
            api_params["tools"][0]["filters"] = {"allowed_domains": [domain]}

        client = OpenAI()
        response = client.responses.create(**api_params)

        logger.debug("Response: %s", pformat(response.output_text, width=160))

        return {"replies": [ChatMessage.from_assistant(response.output_text)]}


EMAIL_INTRO = """\
Hello,

Here is your personalized report with resources your case manager recommends to support your goals.
You've already taken a great first step by exploring these options.

**Your next step**: Look over the resources to see contact info and details about how to get started.
"""


@component
class EmailFullResult:
    """
    Formats JSON object (representing a list of resources and action plan) and sends it to email address.
    """

    @component.output_types(status=str, email=str, message=str)
    def run(self, email: str, resources_dict: dict, action_plan_dict: dict) -> dict:
        logger.info("Emailing result to %s", email)
        logger.debug("Resources JSON content:\n%s", json.dumps(resources_dict, indent=2))
        if action_plan_dict:
            logger.debug("Action plan JSON content:\n%s", json.dumps(action_plan_dict, indent=2))

        formatted_resources = format_resources(resources_dict.get("resources", []))
        formatted_action_plan = format_action_plan(action_plan_dict)

        message = f"{EMAIL_INTRO}\n{formatted_resources}\n\n{formatted_action_plan}"

        # Send email via AWS SES
        subject = "Your Requested Resources and Action Plan"
        success = send_email(recipient=email, subject=subject, body=message)
        status = "success" if success else "failed"

        return {"status": status, "email": email, "message": message}


@component
class EmailResult:
    """
    Formats JSON object (representing a list of resources) and sends it to email address.
    """

    @component.output_types(status=str, email=str, message=str)
    def run(self, email: str, json_dict: dict) -> dict:
        logger.info("Emailing result to %s", email)
        logger.debug("JSON content:\n%s", json.dumps(json_dict, indent=2))
        formatted_resources = format_resources(json_dict.get("resources", []))
        message = f"{EMAIL_INTRO}\n{formatted_resources}"

        # Send email via AWS SES
        subject = "Your Requested Resources"
        success = send_email(recipient=email, subject=subject, body=message)
        status = "success" if success else "failed"

        return {"status": status, "email": email, "message": message}


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


# TODO: Replace with https://docs.haystack.deepset.ai/docs/jsonschemavalidator
@component
class LlmOutputValidator:
    def __init__(self, pydantic_model: type[BaseModelT]):
        # Note that components must be thread-safe, so do not maintain state across runs
        self.pydantic_model = pydantic_model

    @component.output_types(
        valid_replies=List[ChatMessage],
        invalid_replies=Optional[List[ChatMessage]],
        error_message=Optional[str],
    )
    def run(self, replies: List[ChatMessage]) -> dict:
        assert len(replies) == 1, "Expected exactly one reply"
        reply = replies[0]

        try:
            assert reply.text is not None, "Reply text is None"
            output_dict = json.loads(reply.text)
            self.pydantic_model.model_validate(output_dict)
            return {"valid_replies": replies}

        except (ValueError, ValidationError) as e:
            logger.error(
                (
                    "LlmOutputValidator: Invalid JSON from LLM - will try again...\n"
                    "Parsing error: %s\n"
                    "Output from LLM:\n %s \n"
                ),
                e,
                reply,
            )
            return {"invalid_replies": replies, "error_message": str(e)}


@component
class ReadableLogger:
    """Logs input in a human-readable format for debugging purposes."""

    @staticmethod
    def default_mapper(msg: Any) -> Optional[Any]:
        if isinstance(msg, ChatMessage):
            # Don't log 'system' messages
            return msg if msg.role in ["user", "assistant"] else None
        return msg

    def __init__(self, mapper: Optional[Callable] = None) -> None:
        self.mapper = mapper if mapper is not None else self.default_mapper

    @component.output_types(logs=list)
    def run(self, messages_list: Variadic[List]) -> dict:
        logs = []
        for messages in messages_list:
            for item in messages:
                mapped_item = self.mapper(item)
                if mapped_item is None:
                    continue

                if isinstance(mapped_item, ChatMessage):
                    for content in mapped_item._content:
                        logs.append(self.parse_json_if_possible(content))
                else:
                    logs.append(self.parse_json_if_possible(mapped_item))
        return {"logs": logs}

    def parse_json_if_possible(self, content: Any) -> Any:
        if hasattr(content, "text"):
            # Usually for ChatMessage._content[*] but could be for any object with 'text' attribute
            try:
                return json.loads(content.text)
            except JSONDecodeError:
                logger.warning("Failed to parse content as JSON: %s", content.text, exc_info=True)
                return content.text

        return content
