import json
from io import BytesIO
from textwrap import dedent

import pytest
from fastapi import UploadFile
from haystack.dataclasses.chat_message import ChatMessage

from src.adapters import db
from src.common.components import (
    EmailFullResult,
    EmailResult,
    LlmOutputValidator,
    LoadResult,
    LoadSupports,
    ReadableLogger,
    SaveResult,
    UploadFilesToByteStreams,
)
from src.db.models.support_listing import LlmResponse, Support
from src.pipelines.generate_referrals.pipeline_wrapper import ResourceList
from tests.src.db.models.factories import SupportFactory


def test_UploadFilesToByteStreams():
    # Mock UploadFile instances
    file1 = UploadFile(filename="test1.txt", file=BytesIO(b"Hello, World!"))
    file2 = UploadFile(filename="test2.txt", file=BytesIO(b"Another file."))

    # Run
    component = UploadFilesToByteStreams()
    output = component.run(files=[file1, file2])

    # Verify
    byte_streams = output["byte_streams"]
    assert len(byte_streams) == 2
    assert byte_streams[0].meta["filename"] == "test1.txt"
    assert byte_streams[0].data == b"Hello, World!"
    assert byte_streams[1].meta["filename"] == "test2.txt"
    assert byte_streams[1].data == b"Another file."


@pytest.fixture
def support_records(enable_factory_create, db_session: db.Session):
    db_session.query(Support).delete()
    records = [
        SupportFactory.create(name="Support A", description="Desc A", website="http://a.com"),
        SupportFactory.create(name="Support B", description="Desc B", website="http://b.com"),
    ]
    yield records

    for record in records:
        db_session.delete(record)


def test_LoadSupports(support_records, db_session: db.Session):
    component = LoadSupports()
    output = component.run()
    supports = output["supports"]

    assert len(supports) >= 2
    assert any("Name: Support A\n- Description: Desc A" in s for s in supports)
    assert any("Name: Support B\n- Description: Desc B" in s for s in supports)
    assert any("- Website: http://a.com" in s for s in supports)
    assert any("- Website: http://b.com" in s for s in supports)


def test_SaveResult_and_LoadResult(enable_factory_create, db_session: db.Session):
    db_session.query(LlmResponse).delete()

    llm_response = 'This is a test response with JSON: {"somekey": "somevalue"}'
    replies = [ChatMessage.from_assistant(llm_response)]
    component = SaveResult()
    output = component.run(replies=replies)

    result_id = output["result_id"]
    db_record = db_session.query(LlmResponse).filter(LlmResponse.id == result_id).one_or_none()

    assert db_record is not None
    assert db_record.raw_text == llm_response

    # Now test loading it via the LoadResult component
    component = LoadResult()
    output = component.run(result_id=str(result_id))

    result_json = output["result_json"]
    assert result_json == {"somekey": "somevalue"}


def test_EmailResult(enable_factory_create, db_session: db.Session, monkeypatch):
    resources = {
        "resources": [
            {
                "name": "Resource 1",
                "referral_type": "external",
                "description": "Description for Resource 1",
                "website": "http://resource1.com",
                "phones": ["555-1234"],
                "emails": ["resource1@example.com"],
                "addresses": ["123 Main St"],
                "justification": "Justification for Resource 1",
            },
            {
                "name": "Resource 2",
            },
        ]
    }

    # Mock send_email to always return success
    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: True)

    component = EmailResult()
    output = component.run(email="test@example.com", json_dict=resources)

    assert output["status"] == "success"
    assert output["email"] == "test@example.com"
    assert output["message"] == dedent(
        """\
        Hello,

        Here is your personalized report with resources your case manager recommends to support your goals.
        You've already taken a great first step by exploring these options.

        **Your next step**: Look over the resources to see contact info and details about how to get started.

        ### Resource 1
        - Referral Type: external
        - Description: Description for Resource 1
        - Website: http://resource1.com
        - Phone: 555-1234
        - Email: resource1@example.com
        - Addresses: 123 Main St

        ### Resource 2
        - Referral Type: None
        - Description: None
        - Website: None
        - Phone: None
        - Email: None
        - Addresses: None"""
    )


VALID_JSON_OBJ = {
    "resources": [
        {
            "name": "Resource 1",
            "addresses": ["123 Main St"],
            "phones": ["555-1234"],
            "emails": ["resource1@example.com"],
            "website": "http://resource1.com",
            "description": "Description for Resource 1",
            "justification": "Justification for Resource 1",
        },
    ]
}
VALID_JSON_STR = json.dumps(VALID_JSON_OBJ)


def test_LlmOutputValidator():
    component = LlmOutputValidator(pydantic_model=ResourceList)
    valid_replies_output = component.run(replies=[ChatMessage.from_assistant(text=VALID_JSON_STR)])
    assert "valid_replies" in valid_replies_output
    assert valid_replies_output["valid_replies"][0].text == VALID_JSON_STR
    assert "invalid_replies" not in valid_replies_output
    assert "error_message" not in valid_replies_output

    invalid_json_str = f"Based on your query, the resources are:\n{VALID_JSON_STR}"
    invalid_replies_output = component.run(
        replies=[ChatMessage.from_assistant(text=invalid_json_str)]
    )
    assert "valid_replies" not in invalid_replies_output
    assert "invalid_replies" in invalid_replies_output
    assert "error_message" in invalid_replies_output


def test_ReadableLogger():
    manual_logs = [
        {"user_question": "What is the capital of France?"},
    ]
    messages = [
        ChatMessage.from_system("System message"),
        ChatMessage.from_user("User message"),
        ChatMessage.from_assistant("Not a JSON message"),
        ChatMessage.from_assistant(VALID_JSON_STR),
    ]

    component = ReadableLogger()
    output = component.run(messages_list=[manual_logs, messages])

    assert output["logs"] == [
        {"user_question": "What is the capital of France?"},
        "User message",
        "Not a JSON message",
        VALID_JSON_OBJ,
    ]


def test_EmailFullResult_with_resources_and_action_plan(monkeypatch):
    """Test EmailFullResult with both resources and action plan."""
    resources_dict = {
        "resources": [
            {
                "name": "Resource 1",
                "referral_type": "external",
                "description": "Description for Resource 1",
                "website": "http://resource1.com",
                "phones": ["555-1234"],
                "emails": ["resource1@example.com"],
                "addresses": ["123 Main St"],
            },
            {
                "name": "Resource 2",
                "referral_type": "internal",
                "description": "Description for Resource 2",
                "website": "http://resource2.com",
                "phones": ["555-5678", "555-9012"],
                "emails": ["resource2@example.com"],
                "addresses": ["456 Oak Ave"],
            },
        ]
    }

    action_plan_dict = {
        "title": "Your Action Plan",
        "summary": "This is a summary of your action plan.",
        "content": "Step 1: Contact Resource 1\nStep 2: Follow up with Resource 2",
    }

    # Mock send_email to always return success
    email_calls = []

    def mock_send_email(recipient, subject, body):
        email_calls.append({"recipient": recipient, "subject": subject, "body": body})
        return True

    monkeypatch.setattr("src.common.components.send_email", mock_send_email)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    assert output["status"] == "success"
    assert output["email"] == "test@example.com"
    assert "Resource 1" in output["message"]
    assert "Resource 2" in output["message"]
    assert "Your Action Plan" in output["message"]
    assert "This is a summary of your action plan." in output["message"]
    assert "Step 1: Contact Resource 1" in output["message"]

    # Verify email was sent with correct parameters
    assert len(email_calls) == 1
    assert email_calls[0]["recipient"] == "test@example.com"
    assert email_calls[0]["subject"] == "Your Requested Resources and Action Plan"


def test_EmailFullResult_with_empty_resources(monkeypatch):
    """Test EmailFullResult with empty resources list."""
    resources_dict = {"resources": []}

    action_plan_dict = {
        "title": "Your Action Plan",
        "summary": "Summary text",
        "content": "Content text",
    }

    # Mock send_email
    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: True)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    assert output["status"] == "success"
    assert "Your Action Plan" in output["message"]
    # Should not contain any resource headers
    assert "###" not in output["message"]


def test_EmailFullResult_with_missing_resource_fields(monkeypatch):
    """Test EmailFullResult with resources missing optional fields."""
    resources_dict = {
        "resources": [
            {
                "name": "Resource With Missing Fields",
                # Missing all other fields
            }
        ]
    }

    action_plan_dict = {}

    # Mock send_email
    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: True)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    assert output["status"] == "success"
    assert "Resource With Missing Fields" in output["message"]
    assert "- Referral Type: None" in output["message"]
    assert "- Description: None" in output["message"]
    assert "- Website: None" in output["message"]
    assert "- Phone: None" in output["message"]
    assert "- Email: None" in output["message"]
    assert "- Addresses: None" in output["message"]


def test_EmailFullResult_send_email_failure(monkeypatch):
    """Test EmailFullResult when send_email fails."""
    resources_dict = {
        "resources": [
            {
                "name": "Resource 1",
                "referral_type": "external",
                "description": "Description",
                "website": "http://resource1.com",
                "phones": ["555-1234"],
                "emails": ["resource1@example.com"],
                "addresses": ["123 Main St"],
            }
        ]
    }

    action_plan_dict = {
        "title": "Your Action Plan",
        "summary": "Summary",
        "content": "Content",
    }

    # Mock send_email to return failure
    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: False)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    assert output["status"] == "failed"
    assert output["email"] == "test@example.com"
    assert "Resource 1" in output["message"]
    assert "Your Action Plan" in output["message"]


def test_EmailFullResult_with_action_plan_missing_fields(monkeypatch):
    """Test EmailFullResult with action plan missing optional fields."""
    resources_dict = {"resources": []}

    # Test with missing summary
    action_plan_dict = {
        "title": "Action Plan Title",
        "content": "Some content",
    }

    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: True)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    assert output["status"] == "success"
    assert "Action Plan Title" in output["message"]
    assert "Some content" in output["message"]


def test_EmailFullResult_with_action_plan_only_title(monkeypatch):
    """Test EmailFullResult with action plan containing only title."""
    resources_dict = {"resources": []}

    action_plan_dict = {
        "title": "Just A Title",
    }

    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: True)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    assert output["status"] == "success"
    assert "Just A Title" in output["message"]


def test_EmailFullResult_message_format(monkeypatch):
    """Test that EmailFullResult formats the message correctly."""
    resources_dict = {
        "resources": [
            {
                "name": "Test Resource",
                "referral_type": "test_type",
                "description": "Test description",
                "website": "http://test.com",
                "phones": ["111-1111"],
                "emails": ["test@test.com"],
                "addresses": ["Test Address"],
            }
        ]
    }

    action_plan_dict = {
        "title": "Test Plan",
        "summary": "Test summary",
        "content": "Test content",
    }

    monkeypatch.setattr("src.common.components.send_email", lambda **kwargs: True)

    component = EmailFullResult()
    output = component.run(
        email="test@example.com", resources_dict=resources_dict, action_plan_dict=action_plan_dict
    )

    message = output["message"]

    # Check that message starts with EMAIL_INTRO
    assert message.startswith("Hello,")
    assert "Here is your personalized report" in message

    # Check resource formatting
    assert "### Test Resource" in message
    assert "- Referral Type: test_type" in message
    assert "- Description: Test description" in message

    # Check action plan formatting
    assert "## Test Plan" in message
    assert "Test summary" in message
    assert "Test content" in message
