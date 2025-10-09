"Components cannot be defined in pipelines themselves, so define them here."

import logging
from pprint import pformat
from typing import List

from fastapi import UploadFile
from haystack import component
from haystack.dataclasses.byte_stream import ByteStream
from haystack.dataclasses.chat_message import ChatMessage

logger = logging.getLogger(__name__)


@component
class EchoNode:
    "A component that echoes the input"

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
class DummyChatGenerator:
    """
    A dummy chat generator that echoes back the messages used only for development.
    Temporarily replace AmazonBedrockChatGenerator with this to avoid incurring LLM costs.
    """

    @component.output_types(replies=List[ChatMessage])
    def run(self, messages: List[ChatMessage]) -> dict:
        replies = messages
        logger.info("replies: %s", pformat(replies))
        return {"replies": replies}
