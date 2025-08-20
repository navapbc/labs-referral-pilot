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


# def to_chat_messages(
#     msg_list: Sequence[dict | v1.PromptMessage | ChatMessage],
# ) -> list[ChatMessage]:
#     messages = []
#     for msg in msg_list:
#         if isinstance(msg, ChatMessage):
#             chat_msg = msg
#             messages.append(chat_msg)
#             continue
#         elif not isinstance(msg, dict):
#             raise ValueError(f"Expected dict or ChatMessage, got {type(msg)}")

#         role = msg["role"]
#         content = msg["content"]
#         if role == "system":
#             assert isinstance(content, str), f"Expected string, got {type(content)}"
#             chat_msg = ChatMessage.from_system(content)
#         elif role == "user":
#             assert isinstance(content, str), f"Expected string, got {type(content)}"
#             chat_msg = ChatMessage.from_user(content)
#         elif role == "assistant":
#             assert isinstance(content, str), f"Expected string, got {type(content)}"
#             chat_msg = ChatMessage.from_assistant(content)
#         else:
#             raise ValueError(f"Unexpected role: {role} for message {msg}")
#         messages.append(chat_msg)

#     return messages
