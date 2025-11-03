"""Tests for manage_crawl_job module"""
import pytest
from sqlalchemy.orm import Session

from src.db.manage_crawl_job import delete_crawl_job, upsert_crawl_job
from src.db.models.crawl_job import CrawlJob


def test_create_new_crawl_job(db_session: Session):
    """Test creating a new CrawlJob entry"""
    prompt_name = "test_prompt"
    domain = "example.com"
    crawling_interval = 24

    result = upsert_crawl_job(db_session, prompt_name, domain, crawling_interval)

    assert result is not None
    assert result.prompt_name == prompt_name
    assert result.domain == domain
    assert result.crawling_interval == crawling_interval
    assert result.id is not None

    # Verify it was actually saved
    db_session.commit()
    saved_job = db_session.query(CrawlJob).where(CrawlJob.domain == domain).one_or_none()
    assert saved_job is not None
    assert saved_job.id == result.id


def test_update_existing_crawl_job(db_session: Session):
    """Test updating an existing CrawlJob entry"""
    # Create initial job
    domain = "example.com"
    initial_prompt = "initial_prompt"
    initial_interval = 24

    initial_job = upsert_crawl_job(db_session, initial_prompt, domain, initial_interval)
    db_session.commit()
    initial_id = initial_job.id

    # Update the job
    updated_prompt = "updated_prompt"
    updated_interval = 48

    updated_job = upsert_crawl_job(db_session, updated_prompt, domain, updated_interval)

    assert updated_job.id == initial_id  # Same job
    assert updated_job.prompt_name == updated_prompt
    assert updated_job.crawling_interval == updated_interval
    assert updated_job.domain == domain

    # Verify only one job exists
    db_session.commit()
    all_jobs = db_session.query(CrawlJob).where(CrawlJob.domain == domain).all()
    assert len(all_jobs) == 1


def test_upsert_with_invalid_interval_raises_error(db_session: Session):
    """Test that negative or zero intervals raise ValueError"""
    with pytest.raises(ValueError, match="crawling_interval must be a positive integer"):
        upsert_crawl_job(db_session, "test_prompt", "example.com", 0)

    with pytest.raises(ValueError, match="crawling_interval must be a positive integer"):
        upsert_crawl_job(db_session, "test_prompt", "example.com", -5)


def test_delete_existing_job(db_session: Session):
    """Test deleting an existing CrawlJob"""
    domain = "example.com"
    job = upsert_crawl_job(db_session, "test_prompt", domain, 24)
    db_session.commit()
    job_id = job.id

    # Delete the job
    result = delete_crawl_job(db_session, domain)

    assert result is True

    # Verify it was deleted
    db_session.commit()
    deleted_job = db_session.query(CrawlJob).where(CrawlJob.id == job_id).one_or_none()
    assert deleted_job is None


def test_delete_nonexistent_job(db_session: Session):
    """Test deleting a job that doesn't exist returns False"""
    result = delete_crawl_job(db_session, "nonexistent-domain.com")
    assert result is False


def test_delete_one_of_multiple_jobs(db_session: Session):
    """Test deleting one job doesn't affect others"""
    # Create multiple jobs
    domains = ["domain1.com", "domain2.com", "domain3.com"]
    for domain in domains:
        upsert_crawl_job(db_session, "test_prompt", domain, 24)
    db_session.commit()

    # Delete one job
    result = delete_crawl_job(db_session, domains[1])
    assert result is True
    db_session.commit()

    # Verify only the targeted job was deleted
    remaining_jobs = db_session.query(CrawlJob).all()
    assert len(remaining_jobs) == 2
    remaining_domains = {job.domain for job in remaining_jobs}
    assert remaining_domains == {domains[0], domains[2]}


def test_create_crawl_job_without_prompt_name(db_session: Session):
    """Test creating a CrawlJob entry without a prompt_name (for scraper functions)"""
    domain = "scraper-example.com"
    crawling_interval = 24

    result = upsert_crawl_job(db_session, None, domain, crawling_interval)

    assert result is not None
    assert result.prompt_name is None
    assert result.domain == domain
    assert result.crawling_interval == crawling_interval
    assert result.id is not None

    # Verify it was actually saved
    db_session.commit()
    saved_job = db_session.query(CrawlJob).where(CrawlJob.domain == domain).one_or_none()
    assert saved_job is not None
    assert saved_job.id == result.id
    assert saved_job.prompt_name is None


def test_update_crawl_job_to_remove_prompt_name(db_session: Session):
    """Test updating a CrawlJob to remove its prompt_name (switch to scraper)"""
    domain = "example.com"

    # Create job with prompt
    initial_job = upsert_crawl_job(db_session, "initial_prompt", domain, 24)
    db_session.commit()
    initial_id = initial_job.id

    # Update to remove prompt (use scraper instead)
    updated_job = upsert_crawl_job(db_session, None, domain, 48)

    assert updated_job.id == initial_id  # Same job
    assert updated_job.prompt_name is None
    assert updated_job.crawling_interval == 48
    assert updated_job.domain == domain

    # Verify only one job exists
    db_session.commit()
    all_jobs = db_session.query(CrawlJob).where(CrawlJob.domain == domain).all()
    assert len(all_jobs) == 1


def test_update_crawl_job_to_add_prompt_name(db_session: Session):
    """Test updating a CrawlJob to add a prompt_name (switch from scraper to prompt)"""
    domain = "example.com"

    # Create job without prompt (scraper)
    initial_job = upsert_crawl_job(db_session, None, domain, 24)
    db_session.commit()
    initial_id = initial_job.id

    # Update to add prompt
    updated_job = upsert_crawl_job(db_session, "new_prompt", domain, 48)

    assert updated_job.id == initial_id  # Same job
    assert updated_job.prompt_name == "new_prompt"
    assert updated_job.crawling_interval == 48
    assert updated_job.domain == domain

    # Verify only one job exists
    db_session.commit()
    all_jobs = db_session.query(CrawlJob).where(CrawlJob.domain == domain).all()
    assert len(all_jobs) == 1
