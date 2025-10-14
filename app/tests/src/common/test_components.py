from io import BytesIO

import pytest
from fastapi import UploadFile

from src.adapters import db
from src.common.components import LoadSupports, UploadFilesToByteStreams
from src.db.models.support_listing import Support
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
