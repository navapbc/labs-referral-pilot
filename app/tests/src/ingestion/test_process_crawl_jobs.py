from datetime import timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from haystack.dataclasses import ChatMessage

from src.adapters import db
from src.common import haystack_utils
from src.db.models.crawl_job import CrawlJob
from src.db.models.support_listing import Support, SupportListing
from src.ingestion import process_crawl_jobs
from src.util import datetime_util

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_crawl_jobs(db_session: db.Session) -> list[CrawlJob]:
    """Create test crawl jobs with various last_crawled_at states."""
    # Clean up existing jobs first
    db_session.query(CrawlJob).delete()
    db_session.commit()

    now = datetime_util.utcnow()

    # Job that has never been crawled
    job1 = CrawlJob(
        prompt_name="test_prompt",
        domain="example.com",
        crawling_interval=24,
        last_crawled_at=None,
    )
    db_session.add(job1)

    # Job that was crawled more than crawling_interval hours ago (should be processed)
    job2 = CrawlJob(
        prompt_name="test_prompt",
        domain="old-example.com",
        crawling_interval=24,
        last_crawled_at=now - timedelta(hours=25),
    )
    db_session.add(job2)

    # Job that was crawled recently (should not be processed)
    job3 = CrawlJob(
        prompt_name="test_prompt",
        domain="recent-example.com",
        crawling_interval=24,
        last_crawled_at=now - timedelta(hours=12),
    )
    db_session.add(job3)

    # Job with short interval that needs processing
    job4 = CrawlJob(
        prompt_name="test_prompt",
        domain="short-interval.com",
        crawling_interval=1,
        last_crawled_at=now - timedelta(hours=2),
    )
    db_session.add(job4)

    db_session.commit()
    return [job1, job2, job3, job4]


def test_get_jobs_to_process(db_session: db.Session, mock_crawl_jobs: list[CrawlJob]) -> None:
    """Test that get_jobs_to_process correctly filters jobs based on last_crawled_at."""
    jobs = process_crawl_jobs.get_jobs_to_process(db_session)

    # Should return 3 jobs: never crawled, old crawl, and short interval
    assert len(jobs) == 3

    domains = {job.domain for job in jobs}
    assert "example.com" in domains  # Never crawled
    assert "old-example.com" in domains  # Crawled > 24 hours ago
    assert "short-interval.com" in domains  # Crawled > 1 hour ago
    assert "recent-example.com" not in domains  # Recently crawled


def test_get_jobs_to_process_no_jobs(db_session: db.Session) -> None:
    """Test get_jobs_to_process when there are no jobs in the database."""
    # Clean up any existing jobs
    db_session.query(CrawlJob).delete()
    db_session.commit()

    jobs = process_crawl_jobs.get_jobs_to_process(db_session)
    assert jobs == []


def test_get_jobs_to_process_all_recent(db_session: db.Session) -> None:
    """Test get_jobs_to_process when all jobs were recently crawled."""
    # Clean up any existing jobs
    db_session.query(CrawlJob).delete()
    db_session.commit()

    now = datetime_util.utcnow()

    job = CrawlJob(
        prompt_name="test_prompt",
        domain="recent.com",
        crawling_interval=24,
        last_crawled_at=now - timedelta(hours=1),
    )
    db_session.add(job)
    db_session.commit()

    jobs = process_crawl_jobs.get_jobs_to_process(db_session)
    assert len(jobs) == 0


async def test_call_openai_with_web_search() -> None:
    """Test calling OpenAI API with web_search tool."""
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()

    # Set up mock response
    support_data = [
        {
            "name": "Test Support",
            "website": "https://test.com",
            "emails": ["test@example.com"],
            "addresses": ["123 Test St"],
            "phone_numbers": ["555-1234"],
            "description": "Test description",
        }
    ]
    mock_message.content = str(support_data).replace("'", '"')
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    # Create mock prompt template
    prompt_template = [
        ChatMessage.from_system("{{schema}}"),
        ChatMessage.from_user("Search for support resources"),
    ]

    schema = {"type": "object"}

    # Call the function
    result = await process_crawl_jobs.call_openai_with_web_search(
        prompt_template, "example.com", schema, mock_client
    )

    # Verify result
    assert len(result) == 1
    assert result[0]["name"] == "Test Support"
    assert result[0]["website"] == "https://test.com"

    # Verify OpenAI client was called correctly
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args

    assert call_args.kwargs["model"] == "o3-mini"
    assert call_args.kwargs["reasoning_effort"] == "high"
    assert "web_search" in str(call_args.kwargs["tools"])


async def test_process_single_job(monkeypatch) -> None:
    """Test processing a single crawl job."""
    # Create a test job
    job = CrawlJob(
        id=uuid4(),
        prompt_name="test_prompt",
        domain="example.com",
        crawling_interval=24,
        last_crawled_at=None,
    )

    # Mock get_phoenix_prompt
    mock_prompt = [
        ChatMessage.from_system("{{schema}}"),
        ChatMessage.from_user("Find support resources"),
    ]
    monkeypatch.setattr(haystack_utils, "get_phoenix_prompt", lambda name: mock_prompt)

    # Mock OpenAI call
    async def mock_openai_call(prompt, domain, schema, client):
        return [
            {
                "name": "Support 1",
                "website": None,
                "emails": [],
                "addresses": ["123 Main St"],
                "phone_numbers": ["555-1234"],
                "description": "Test support",
            },
            {
                "name": "Support 2",
                "website": "https://support2.com",
                "emails": ["info@support2.com"],
                "addresses": [],
                "phone_numbers": [],
                "description": "Another support",
            },
        ]

    monkeypatch.setattr(process_crawl_jobs, "call_openai_with_web_search", mock_openai_call)

    # Mock client
    mock_client = AsyncMock()

    # Process the job
    result_job, support_entries = await process_crawl_jobs.process_single_job(job, mock_client)

    # Verify results
    assert result_job == job
    assert len(support_entries) == 2
    assert "Support 1" in support_entries
    assert "Support 2" in support_entries
    assert support_entries["Support 1"].addresses == ["123 Main St"]
    assert support_entries["Support 2"].website == "https://support2.com"


def test_save_job_results_new_listing(db_session: db.Session) -> None:
    """Test saving job results when the listing doesn't exist yet."""
    # Clean up existing data
    db_session.query(CrawlJob).delete()
    db_session.query(Support).delete()
    db_session.query(SupportListing).delete()
    db_session.commit()

    # Create a job
    job = CrawlJob(
        prompt_name="test_prompt",
        domain="example.com",
        crawling_interval=24,
        last_crawled_at=None,
    )
    db_session.add(job)
    db_session.commit()

    # Create support entries
    support_entries = [
        process_crawl_jobs.SupportEntry(
            name="Test Support",
            website="https://test.com",
            emails=["test@example.com"],
            addresses=["123 Test St"],
            phone_numbers=["555-1234"],
            description="Test description",
        ),
    ]

    # Save results
    before_time = datetime_util.utcnow()
    process_crawl_jobs.save_job_results(db_session, job, support_entries)
    after_time = datetime_util.utcnow()

    # Verify SupportListing was created
    listing = (
        db_session.query(SupportListing)
        .where(SupportListing.name == f"Crawl Job: {job.domain}")
        .one()
    )
    assert listing.uri == job.domain

    # Verify Support was created
    supports = db_session.query(Support).where(Support.support_listing_id == listing.id).all()
    assert len(supports) == 1
    assert supports[0].name == "Test Support"
    assert supports[0].addresses == ["123 Test St"]

    # Verify last_crawled_at was updated
    db_session.refresh(job)
    assert job.last_crawled_at is not None
    assert before_time <= job.last_crawled_at <= after_time


def test_save_job_results_existing_listing(db_session: db.Session) -> None:
    """Test saving job results when the listing already exists."""
    # Clean up existing data
    db_session.query(CrawlJob).delete()
    db_session.query(Support).delete()
    db_session.query(SupportListing).delete()
    db_session.commit()

    # Create a job
    job = CrawlJob(
        prompt_name="test_prompt",
        domain="example.com",
        crawling_interval=24,
        last_crawled_at=None,
    )
    db_session.add(job)

    # Create existing listing with old supports
    listing_name = f"Crawl Job: {job.domain}"
    existing_listing = SupportListing(name=listing_name, uri="old-uri")
    db_session.add(existing_listing)
    db_session.flush()

    old_support = Support(
        support_listing_id=existing_listing.id,
        name="Old Support",
        addresses=["Old Address"],
        phone_numbers=[],
        email_addresses=[],
        description=None,
        website=None,
    )
    db_session.add(old_support)
    db_session.commit()

    # Create new support entries
    support_entries = [
        process_crawl_jobs.SupportEntry(
            name="New Support",
            website=None,
            emails=[],
            addresses=["New Address"],
            phone_numbers=[],
            description="New description",
        ),
    ]

    # Save results
    process_crawl_jobs.save_job_results(db_session, job, support_entries)

    # Verify listing was updated
    db_session.refresh(existing_listing)
    assert existing_listing.uri == job.domain

    # Verify old support was deleted and new one added
    supports = (
        db_session.query(Support).where(Support.support_listing_id == existing_listing.id).all()
    )
    assert len(supports) == 1
    assert supports[0].name == "New Support"
    assert supports[0].addresses == ["New Address"]

    # Verify there's only one listing
    all_listings = db_session.query(SupportListing).all()
    assert len(all_listings) == 1


# Note: Integration tests for process_all_jobs() and main() are intentionally
# excluded as per requirements. The individual functions are tested above,
# and process_all_jobs() orchestrates them - it should be tested manually or
# through end-to-end tests.
