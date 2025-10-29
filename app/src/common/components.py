"Components cannot be defined in pipelines themselves, so define them here."

import json
import logging
from pprint import pformat
from typing import List

from fastapi import UploadFile
from haystack import component
from haystack.dataclasses.byte_stream import ByteStream
from haystack.dataclasses.chat_message import ChatMessage
from openai import OpenAI

from src.app_config import config
from src.db.models.support_listing import LlmResponse, Support

logger = logging.getLogger(__name__)


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

    @component.output_types(response=str)
    def run(
        self,
        messages: list[ChatMessage],
        domain: str,
        model: str = "gpt-5",
        reasoning_effort: str = "high",
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
            "tools": [{"type": "web_search", "filters": {"allowed_domains": [domain]}}],
        }

        client = OpenAI()
        response = client.responses.create(**api_params)

        logger.debug("Response: %s", pformat(response.output_text, width=160))

        return {"response": response.output_text}


@component
class EmailResult:
    """
    Formats JSON object (representing a list of resources) and sends it to email address.
    """

    @component.output_types(status=str, email=str, message=str)
    def run(self, email: str, json_dict: dict) -> dict:
        logger.info("Emailing result to %s", email)
        logger.info("JSON content:\n%s", json.dumps(json_dict, indent=2))
        formatted_resources = self.format_resources(json_dict.get("resources", []))
        message = f"Here are the resources you requested:\n\n{formatted_resources}"
        # TODO: call email service to send email
        return {"status": "success", "email": email, "message": message}

    def format_resources(self, resources: list[dict]) -> str:
        return "\n\n".join([self.format_resource(resource) for resource in resources])

    def format_resource(self, resource: dict) -> str:
        return "\n".join(
            [
                f"{resource.get('name', 'Unnamed Resource')}",
                f"- Referral Type: {resource.get('referral_type', 'None')}",
                f"- Description: {resource.get('description', 'None')}",
                f"- Website: {resource.get('website', 'None')}",
                f"- Phone: {', '.join(resource.get('phones', ['None']))}",
                f"- Email: {', '.join(resource.get('emails', ['None']))}",
                f"- Addresses: {', '.join(resource.get('addresses', ['None']))}",
                f"- Justification: {resource.get('justification', 'None')}",
            ]
        )
