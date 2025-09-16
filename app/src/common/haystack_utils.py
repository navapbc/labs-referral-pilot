from typing import Sequence

from haystack.dataclasses.chat_message import ChatMessage
from phoenix.client.__generated__ import v1


def to_chat_messages(
    msg_list: Sequence[dict | v1.PromptMessage | ChatMessage],
) -> list[ChatMessage]:
    messages = []
    for msg in msg_list:
        if isinstance(msg, ChatMessage):
            chat_msg = msg
            messages.append(chat_msg)
            continue
        elif not isinstance(msg, dict):
            raise ValueError(f"Expected dict or ChatMessage, got {type(msg)}")

        role = msg["role"]
        content = msg["content"]

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
