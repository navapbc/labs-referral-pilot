"Components cannot be defined in pipelines themselves, so define them here."

import logging
from pprint import pformat
from typing import List

from fastapi import UploadFile
from haystack import component
from haystack.dataclasses.byte_stream import ByteStream
from haystack.dataclasses.chat_message import ChatMessage

from src.app_config import config
from src.db.models.support_listing import Support

from src.common import haystack_utils

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
class GetPhoenixPrompt:

    @component.output_types(prompt=list[ChatMessage])
    def run(self, pipeline_name: str, prompt_version_id: str) -> list[ChatMessage]:
        prompt = haystack_utils.get_phoenix_prompt(pipeline_name, prompt_version_id)
        return prompt

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
