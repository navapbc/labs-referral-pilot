import pytest
from haystack import component
from haystack.dataclasses import ChatMessage, Document

from src.adapters import db
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
    "urls": [],
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
    "urls": [],
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
    "urls": [
      "http://www.austinecho.org/ca"
    ],
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
    "urls": [],
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
    extract_supports.save_to_db(db_session, support_listing, {})
    assert db_session.query(SupportListing).count() == 1
    listing_record = (
        db_session.query(SupportListing).where(SupportListing.name == name).one_or_none()
    )
    assert listing_record.uri == "some/path/to/file.pdf"

    # Update the record
    support_listing = SupportListing(name=name, uri="different/path/to/file.pdf")
    extract_supports.save_to_db(db_session, support_listing, {})
    assert db_session.query(SupportListing).count() == 1
    listing_record = (
        db_session.query(SupportListing).where(SupportListing.name == name).one_or_none()
    )
    assert listing_record.uri == "different/path/to/file.pdf"
