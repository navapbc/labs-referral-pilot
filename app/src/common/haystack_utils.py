import uuid
from typing import Sequence

from haystack.dataclasses.chat_message import ChatMessage
from phoenix.client.__generated__ import v1

from src.common import phoenix_utils


def get_phoenix_prompt(prompt_name: str, prompt_version_id: str = "default") -> list[ChatMessage]:
    prompt_ver = phoenix_utils.get_prompt_template(prompt_name, prompt_version_id)
    return to_chat_messages(prompt_ver._template["messages"])


def to_chat_messages(
    msg_list: Sequence[dict | v1.PromptMessage | ChatMessage],
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

        assert isinstance(content, list), f"Expected list content, got {type(content)}: {content}"
        assert len(content) == 1, f"Expected single content, got {len(content)} items: {content}"
        assert content[0]["type"] == "text", f"Expected text content, got {content[0]['type']}"
        assert "text" in content[0], f"Expected 'text' in content[0], got {content[0]}"
        text = content[0]["text"]

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
