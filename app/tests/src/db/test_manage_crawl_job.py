"""Tests for manage_crawl_job module"""
import pytest
from sqlalchemy.orm import Session

from src.db.manage_crawl_job import delete_crawl_job, upsert_crawl_job
from src.db.models.crawl_job import CrawlJob


class TestUpsertCrawlJob:
    """Tests for upsert_crawl_job function"""

    def test_create_new_crawl_job(self, db_session: Session):
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

    def test_update_existing_crawl_job(self, db_session: Session):
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

    def test_upsert_with_invalid_interval_raises_error(self, db_session: Session):
        """Test that negative or zero intervals raise ValueError"""
        with pytest.raises(ValueError, match="crawling_interval must be a positive integer"):
            upsert_crawl_job(db_session, "test_prompt", "example.com", 0)

        with pytest.raises(ValueError, match="crawling_interval must be a positive integer"):
            upsert_crawl_job(db_session, "test_prompt", "example.com", -5)

    def test_upsert_multiple_domains(self, db_session: Session):
        """Test creating multiple CrawlJobs with different domains"""
        jobs_data = [
            ("prompt1", "domain1.com", 12),
            ("prompt2", "domain2.com", 24),
            ("prompt3", "domain3.com", 48),
        ]

        created_jobs = []
        for prompt_name, domain, interval in jobs_data:
            job = upsert_crawl_job(db_session, prompt_name, domain, interval)
            created_jobs.append(job)

        db_session.commit()

        # Verify all jobs were created
        assert len(created_jobs) == 3
        assert all(job.id is not None for job in created_jobs)

        # Verify domains are unique
        domains = [job.domain for job in created_jobs]
        assert len(set(domains)) == 3


class TestDeleteCrawlJob:
    """Tests for delete_crawl_job function"""

    def test_delete_existing_job(self, db_session: Session):
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

    def test_delete_nonexistent_job(self, db_session: Session):
        """Test deleting a job that doesn't exist returns False"""
        result = delete_crawl_job(db_session, "nonexistent-domain.com")
        assert result is False

    def test_delete_one_of_multiple_jobs(self, db_session: Session):
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


class TestUpsertAndDeleteIntegration:
    """Integration tests for upsert and delete operations"""

    def test_delete_and_recreate(self, db_session: Session):
        """Test that a deleted job can be recreated"""
        domain = "example.com"
        prompt1 = "prompt1"
        interval1 = 24

        # Create job
        job1 = upsert_crawl_job(db_session, prompt1, domain, interval1)
        db_session.commit()
        original_id = job1.id

        # Delete job
        delete_result = delete_crawl_job(db_session, domain)
        assert delete_result is True
        db_session.commit()

        # Recreate job
        prompt2 = "prompt2"
        interval2 = 48
        job2 = upsert_crawl_job(db_session, prompt2, domain, interval2)
        db_session.commit()

        # Should be a new job with different ID
        assert job2.id != original_id
        assert job2.prompt_name == prompt2
        assert job2.crawling_interval == interval2

    def test_upsert_after_failed_delete(self, db_session: Session):
        """Test that upsert works correctly even after a failed delete"""
        domain = "unique-domain-for-this-test.com"

        # Try to delete non-existent job
        delete_result = delete_crawl_job(db_session, domain)
        assert delete_result is False

        # Create job should still work
        job = upsert_crawl_job(db_session, "test_prompt", domain, 24)
        db_session.commit()

        assert job is not None
        assert job.domain == domain
