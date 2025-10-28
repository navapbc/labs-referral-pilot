from datetime import timedelta
from uuid import uuid4

import pytest
from haystack import component

from src.adapters import db
from src.common import phoenix_utils
from src.db.models.crawl_job import CrawlJob
from src.db.models.support_listing import Support, SupportListing
from src.ingestion import process_crawl_jobs
from src.util import datetime_util


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
    assert {job.domain for job in jobs} == {"example.com", "old-example.com", "short-interval.com"}


def test_get_jobs_to_process_no_jobs(db_session: db.Session) -> None:
    """Test get_jobs_to_process when there are no jobs in the database."""
    # Clean up any existing jobs
    db_session.query(CrawlJob).delete()
    db_session.commit()

    jobs = process_crawl_jobs.get_jobs_to_process(db_session)
    assert jobs == []


@component
class MockOpenAIGenerator:
    def __init__(self):
        pass

    @component.output_types(response=str)
    def run(
        self, prompt: str, model: str, reasoning_effort: str, domain: str | None = None
    ) -> dict:
        # Return mock response based on domain
        if domain == "example1.com":
            response = """[{"name": "Support for example1.com", "website": "https://example1.com", "emails": ["info@example1.com"], "addresses": ["123 Main St"], "phone_numbers": ["555-1234"], "description": "Test support for example1.com"}]"""
        else:
            response = """[{"name": "Support for example2.com", "website": "https://example2.com", "emails": [], "addresses": ["456 Oak Ave"], "phone_numbers": [], "description": "Test support for example2.com"}]"""
        return {"response": response}


def test_process_crawl_jobs(monkeypatch) -> None:
    """Test processing multiple crawl jobs with mocked pipeline."""
    # Create test jobs
    job1 = CrawlJob(
        id=uuid4(),
        prompt_name="test_prompt",
        domain="example1.com",
        crawling_interval=24,
        last_crawled_at=None,
    )
    job2 = CrawlJob(
        id=uuid4(),
        prompt_name="test_prompt",
        domain="example2.com",
        crawling_interval=24,
        last_crawled_at=None,
    )

    monkeypatch.setattr(process_crawl_jobs, "create_websearch", lambda: MockOpenAIGenerator())
    monkeypatch.setattr(
        phoenix_utils,
        "get_prompt_template",
        lambda _: type(
            "Mock", (), {"_template": {"messages": [{"content": [{"text": "hello"}]}]}}
        )(),
    )

    # Process the jobs
    results = process_crawl_jobs.process_crawl_jobs([job1, job2])

    # Verify results
    assert len(results) == 2

    # Check first job results
    result_job1, support_entries1 = results[0]
    assert result_job1.domain == "example1.com"
    assert len(support_entries1) == 1
    assert "Support for example1.com" in support_entries1
    assert support_entries1["Support for example1.com"].addresses == ["123 Main St"]

    # Check second job results
    result_job2, support_entries2 = results[1]
    assert result_job2.domain == "example2.com"
    assert len(support_entries2) == 1
    assert "Support for example2.com" in support_entries2
    assert support_entries2["Support for example2.com"].addresses == ["456 Oak Ave"]


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
    existing_listing = SupportListing(name=listing_name, uri="example.com")
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
