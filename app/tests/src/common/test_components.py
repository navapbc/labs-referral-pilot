from io import BytesIO
from textwrap import dedent

import pytest
from fastapi import UploadFile
from haystack.dataclasses.chat_message import ChatMessage

from src.adapters import db
from src.common.components import (
    EmailResult,
    LoadResult,
    LoadSupports,
    SaveResult,
    UploadFilesToByteStreams,
)
from src.db.models.support_listing import LlmResponse, Support
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


def test_EmailResult(enable_factory_create, db_session: db.Session):
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

    component = EmailResult()
    output = component.run(email="test@example.com", json_dict=resources)

    assert output["status"] == "success"
    assert output["email"] == "test@example.com"
    assert output["message"] == dedent(
        """\
        Here are the resources you requested:

        Resource 1
        - Referral Type: external
        - Description: Description for Resource 1
        - Website: http://resource1.com
        - Phone: 555-1234
        - Email: resource1@example.com
        - Addresses: 123 Main St
        - Justification: Justification for Resource 1

        Resource 2
        - Referral Type: None
        - Description: None
        - Website: None
        - Phone: None
        - Email: None
        - Addresses: None
        - Justification: None"""
    )
