import boto3
import pytest
from haystack import component
from haystack.dataclasses import ChatMessage, Document
from moto import mock_s3

from src.adapters import db
from src.common import haystack_utils
from src.db.models.support_listing import SupportListing
from src.ingestion import extract_supports


@pytest.fixture
def document() -> Document:
    # Spaces on blank lines are intentional to mimic PDF content
    content = """Travis County Basic Needs Resource & Referral Guide

BASIC NEEDS RESOURCES:
All Saints Episcopal Church
209 W 27th St. Austin. TX 78705
(512) 476-3589
All Saints provides assistance on Tuesdays only, 1st come, 1st served.
• Greyhound bus tickets up to 25 dollars.
• ID/Birth Certificates
• Payment of utility bills up to 20.00 dollars
• Rent, rental deposits up to 20.00 dollars
• Prescriptions. medical bills and eyeglasses
• HEB gift cards
  
First Baptist Church of Austin
90 I Trinity St, Austin. TX 7870 I
(512) 476-2625
Call for an appointment for the 1st Monday of each month.
• •Partial assistance with Greyhound Bus tickets (with pledges from other
churches to cover full amount)
• •TX ID. Birth Certificates and Driver's License.
  
 Foundation for the Homeless
1300 Lavaca Street. Austin. TX 7870 I
1611 Headway Circle building 2. Austin, TX 78754
(512) 453-6570
Services are provided on Tuesdays and Thursdays only. 5am-6:30am with breakfast being
served at 6am. First come, first served.
• TX ID. Birth Certificates and Driver's License
• Capital Metro Disability Card

Baptist Community Center
2000 East 2nd Street 78702
(512) 472-7592
Call for an appointment Monday through Friday (8:30am-l2noon * lpm-5pm). To receive
services. bring photo ID, SS card
"""  # noqa: W293
    return Document(content=content)


def test_split_doc(document: Document) -> None:
    split_docs = extract_supports.split_doc(document, passages_per_doc=2, overlap=1)
    assert len(split_docs) == 4

    # Check content and overlap
    assert split_docs[0].content
    assert "Travis County Basic Needs Resource & Referral Guide" in split_docs[0].content
    assert "All Saints Episcopal Church" in split_docs[0].content

    assert split_docs[1].content
    assert "All Saints Episcopal Church" in split_docs[1].content
    assert "First Baptist Church of Austin" in split_docs[1].content

    assert split_docs[2].content
    assert "First Baptist Church of Austin" in split_docs[2].content
    assert "Foundation for the Homeless" in split_docs[2].content

    assert split_docs[3].content
    assert "Foundation for the Homeless" in split_docs[3].content
    assert "Baptist Community Center" in split_docs[3].content


MOCK_LLM_RESPONSE = """[
  {
    "name": "All Saints Episcopal Church",
    "website": null,
    "emails": [],
    "addresses": [
      "209 W 27th St. Austin. TX 78705"
    ],
    "phone_numbers": [
      "(512) 476-3589"
    ],
    "description": "Provides various assistance services on Tuesdays only, first come first served. Offers help with bus tickets, ID/birth certificates, utility bills, rent, prescriptions, gasoline, work boots, background checks, and HEB gift cards."
  },
  {
    "name": "First Baptist Church of Austin",
    "website": null,
    "emails": [],
    "addresses": [
      "901 Trinity St, Austin. TX 78701"
    ],
    "phone_numbers": [
      "(512) 476-2625"
    ],
    "description": "Offers assistance by appointment on the first Monday of each month. Services include partial Greyhound bus tickets, ID assistance, prescription co-pays, gas cards, and 30-day bus passes."
  },
  {
    "name": "Foundation for the Homeless",
    "website": null,
    "emails": [
      "info@foundationhomeless.org"
    ],
    "addresses": [
      "PO Box 140946, Austin, TX 78714",
      "1300 Lavaca Street, Austin, TX"
    ],
    "phone_numbers": [
      "512-453-6570"
    ],
    "description": "Provides hot breakfasts, basic medical screening, eyeglasses, and assistance with identification documentation for individuals and families. Operates the Family Rehousing Initiative (FRI) program offering housing-focused shelter and rapid rehousing for families with children experiencing homelessness."
  },
  {
    "name": "Baptist Community Center",
    "website": null,
    "emails": [],
    "addresses": [
      "2000 East 2nd Street, Austin, Texas 78702"
    ],
    "phone_numbers": [
      "512-478-7243"
    ],
    "description": "A thrift store operating Wednesdays from 8:30 a.m. to 12 p.m. Offers low-cost clothing including baby, work, children, and adult apparel."
  }
]"""


@component
class MockLLM:
    def __init__(self):
        self.llm = None

    @component.output_types(replies=list[ChatMessage])
    def run(self, prompt: list[ChatMessage]) -> dict[str, list[ChatMessage]]:
        return {"replies": [ChatMessage.from_assistant(MOCK_LLM_RESPONSE)]}


def test_extract_support_entries(monkeypatch, document: Document) -> None:
    monkeypatch.setattr(extract_supports, "create_llm", lambda: MockLLM())
    monkeypatch.setattr(
        haystack_utils,
        "get_phoenix_prompt",
        lambda _prompt_name: [
            ChatMessage.from_system("{{schema}}"),
            ChatMessage.from_user("{{doc}}"),
        ],
    )

    supports = extract_supports.extract_support_entries("Test Support Listing", document)
    assert len(supports) == 4
    assert supports["All Saints Episcopal Church"].addresses == ["209 W 27th St. Austin. TX 78705"]
    assert supports["First Baptist Church of Austin"].addresses == [
        "901 Trinity St, Austin. TX 78701"
    ]
    assert supports["Foundation for the Homeless"].addresses == [
        "PO Box 140946, Austin, TX 78714",
        "1300 Lavaca Street, Austin, TX",
    ]
    assert supports["Baptist Community Center"].addresses == [
        "2000 East 2nd Street, Austin, Texas 78702"
    ]


def test_save_to_db(db_session: db.Session):
    db_session.query(SupportListing).delete()

    # Add new DB record
    name = "Test Support Listing"
    support_listing = SupportListing(name=name, uri="some/path/to/file.pdf")
    support_entries = [
        extract_supports.SupportEntry(
            name="Episcopal Church",
            website=None,
            emails=[],
            addresses=["209 W 27th St. Austin. TX 78705"],
            phone_numbers=["(512) 476-3589"],
            description="Provides various assistance services.",
        ),
        extract_supports.SupportEntry(
            name="First Baptist Church of Austin",
            website=None,
            emails=[],
            addresses=[],
            phone_numbers=[],
            description=None,
        ),
    ]
    extract_supports.save_to_db(db_session, support_listing, support_entries)

    # Check the SupportListing
    assert db_session.query(SupportListing).count() == 1
    listing_record = (
        db_session.query(SupportListing).where(SupportListing.name == name).one_or_none()
    )
    assert listing_record.uri == "some/path/to/file.pdf"

    # Check the Support records
    supports = {support.name: support for support in listing_record.supports}
    assert len(supports) == 2
    assert supports["Episcopal Church"].addresses == ["209 W 27th St. Austin. TX 78705"]
    assert supports["First Baptist Church of Austin"].addresses == []
    assert supports["Episcopal Church"].description == "Provides various assistance services."
    assert supports["First Baptist Church of Austin"].description is None

    # Now update the SupportListing record URI with 1 support entry
    support_listing = SupportListing(name=name, uri="different/path/to/file.pdf")
    support_entry = extract_supports.SupportEntry(
        name="Replacement",
        website=None,
        emails=[],
        addresses=[],
        phone_numbers=[],
        description="Replacement description",
    )

    # Check the updated SupportListing
    extract_supports.save_to_db(db_session, support_listing, [support_entry])
    assert db_session.query(SupportListing).count() == 1
    listing_record = (
        db_session.query(SupportListing).where(SupportListing.name == name).one_or_none()
    )
    assert listing_record.uri == "different/path/to/file.pdf"

    # Check the new Support record
    db_session.refresh(listing_record)
    supports = {support.name: support for support in listing_record.supports}
    assert len(supports) == 1
    assert supports["Replacement"].description == "Replacement description"


def test_extract_from_pdf_file_not_found():
    """Test that FileNotFoundError is raised when file doesn't exist locally and smart_open fails."""
    nonexistent_path = "/path/to/nonexistent/file.pdf"

    with pytest.raises(FileNotFoundError, match="File not found: /path/to/nonexistent/file.pdf"):
        extract_supports.extract_from_pdf(nonexistent_path)


def test_extract_from_pdf_smart_open_exception():
    """Test that FileNotFoundError is raised when smart_open throws an exception."""
    # Test with an invalid S3 URI that will cause smart_open to fail
    invalid_s3_uri = "s3://nonexistent-bucket/nonexistent-file.pdf"

    with pytest.raises(
        FileNotFoundError, match="File not found: s3://nonexistent-bucket/nonexistent-file.pdf"
    ):
        extract_supports.extract_from_pdf(invalid_s3_uri)


@mock_s3
def test_extract_from_pdf_with_s3_file():
    # Create mock S3 bucket and upload the sample PDF
    bucket_name = "test-bucket"
    key = "test-files/SampleBasicNeedsGuide.pdf"
    s3_uri = f"s3://{bucket_name}/{key}"

    # Set up mock S3
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=bucket_name)

    # Read the sample PDF and upload to mock S3
    with open("tests/sample_data/SampleBasicNeedsGuide.pdf", "rb") as f:
        pdf_content = f.read()

    s3_client.put_object(Bucket=bucket_name, Key=key, Body=pdf_content)

    # Test extracting from S3 URI
    document = extract_supports.extract_from_pdf(s3_uri)

    # Verify the document was extracted successfully
    assert document is not None
    assert document.content is not None
    assert len(document.content) > 0

    # Verify it contains expected content from the PDF
    assert "Hope" in document.content and "Harbor" in document.content
