"Components cannot be defined in pipelines themselves, so define them here."

import logging
from pprint import pformat
from typing import List

from haystack import component
from haystack.dataclasses.chat_message import ChatMessage

logger = logging.getLogger(__name__)


@component
# Define a custom node that just echoes the input
class EchoNode:
    "A component that echoes the input"

    @component.output_types(full_prompt=List[ChatMessage])
    def run(self, prompt: List[ChatMessage], history: List[ChatMessage]) -> dict:
        full_prompt = history + prompt
        logger.info("Full prompt: %s", pformat(full_prompt))
        return {"full_prompt": full_prompt}
