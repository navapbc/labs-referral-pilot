"Process scheduled crawl jobs by extracting support resources from domains using OpenAI web search."

import asyncio
import json
import logging
from typing import Iterable

from haystack import AsyncPipeline
from haystack.components.builders import ChatPromptBuilder
from sqlalchemy import func, or_

from src.adapters import db
from src.app_config import config
from src.common import haystack_utils
from src.common.components import OpenAIWebSearchGenerator
from src.db.models.crawl_job import CrawlJob
from src.db.models.support_listing import Support, SupportListing
from src.ingestion.support_entry import SUPPORT_ENTRY_SCHEMA, SupportEntry
from src.util import datetime_util

logger = logging.getLogger(__name__)


def create_websearch() -> OpenAIWebSearchGenerator:
    return OpenAIWebSearchGenerator()


def build_pipeline() -> AsyncPipeline:
    """
    Build a Haystack pipeline for processing crawl jobs.

    Args:
        prompt_name: Name of the Phoenix prompt to use

    Returns:
        Configured AsyncPipeline
    """
    pipe = AsyncPipeline()
    pipe.add_component("prompt_builder", ChatPromptBuilder(variables=["schema"]))
    pipe.add_component("llm", create_websearch())
    pipe.connect("prompt_builder", "llm.messages")
    return pipe


async def run_pipeline(pipeline: AsyncPipeline, job: CrawlJob) -> list[dict]:
    """
    Run the pipeline for a single crawl job.

    Args:
        pipeline: The Haystack AsyncPipeline to run
        job: The CrawlJob to process

    Returns:
        List of support entry dictionaries
    """

    # TODO: Add scraping functionality in follow up PR
    if job.prompt_name is None:
        raise NotImplementedError()

    logger.info("Running pipeline for job: domain=%s, prompt=%s", job.domain, job.prompt_name)

    prompt_template = haystack_utils.get_phoenix_prompt(job.prompt_name)

    _result = await pipeline.run_async(
        {
            "prompt_builder": {
                "template": prompt_template,
                "schema": SUPPORT_ENTRY_SCHEMA,
            },
            "llm": {
                "domain": job.domain,
                "model": "gpt-5",
                "reasoning_effort": "high",
            },
        }
    )

    response = _result["llm"]["replies"][0]._content[0].text

    logger.info("Finished pipeline for domain: %s", job.domain)
    logger.info(response)

    support_entries = json.loads(response)
    logger.info("Number of support entries for %s: %d", job.domain, len(support_entries))
    logger.debug("Support entry names: %s", [entry["name"] for entry in support_entries])

    return support_entries


async def run_pipeline_and_join_results(
    pipeline: AsyncPipeline, jobs: list[CrawlJob]
) -> list[tuple[CrawlJob, dict[str, SupportEntry]]]:
    """
    Run the pipeline for each job in parallel and join the results.

    Individual job failures are logged but do not prevent other jobs from processing.

    Args:
        pipeline: The Haystack AsyncPipeline to run
        jobs: List of CrawlJob instances to process

    Returns:
        List of tuples (job, support_entries_dict) for successfully processed jobs
    """
    tasks = [run_pipeline(pipeline, job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine jobs with their results and convert to SupportEntry objects
    job_results = []
    for job, result in zip(jobs, results):
        if isinstance(result, BaseException):
            logger.error(
                "Failed to process job for domain %s: %s",
                job.domain,
                result,
                exc_info=result,
            )
            continue

        # Deduplicate by name
        support_entries = {entry["name"]: SupportEntry(**entry) for entry in result}
        job_results.append((job, support_entries))

    return job_results


def get_jobs_to_process(db_session: db.Session) -> list[CrawlJob]:
    """
    Get all crawl jobs that need processing.

    A job needs processing if:
    - last_crawled_at is null (never crawled), OR
    - last_crawled_at is more than crawling_interval hours ago
    """
    now = datetime_util.utcnow()

    # Query for jobs that need processing:
    # - last_crawled_at is null (never crawled), OR
    # - last_crawled_at is more than crawling_interval hours ago
    jobs_to_process = (
        db_session.query(CrawlJob)
        .filter(
            or_(
                CrawlJob.last_crawled_at.is_(None),
                CrawlJob.last_crawled_at
                <= now - func.make_interval(0, 0, 0, 0, CrawlJob.crawling_interval),
            )
        )
        .all()
    )

    logger.info("Found %d jobs to process", len(jobs_to_process))
    return jobs_to_process


def save_job_results(
    db_session: db.Session,
    job: CrawlJob,
    support_entries: Iterable[SupportEntry],
) -> None:
    """
    Save the results of a crawl job to the database.

    This will:
    1. Create or update the SupportListing with uri=domain and name=f"Crawl Job: {domain}"
    2. Delete all existing Support records for that SupportListing
    3. Add new Support records from the crawl results
    4. Update the job's last_crawled_at timestamp

    Args:
        db_session: Database session
        job: CrawlJob instance that was processed
        support_entries: Iterable of SupportEntry objects to save
    """
    listing_name = f"Crawl Job: {job.domain}"

    # Find or create the SupportListing
    support_listing = (
        db_session.query(SupportListing).where(SupportListing.name == listing_name).one_or_none()
    )

    if support_listing:
        logger.info(
            "Deleting Support records associated with existing SupportListing: %r", listing_name
        )
        db_session.query(Support).where(Support.support_listing_id == support_listing.id).delete()
    else:
        logger.info("Creating new SupportListing: %r", listing_name)
        support_listing = SupportListing(name=listing_name, uri=job.domain)
        db_session.add(support_listing)

    # Add new Support records
    for support in support_entries:
        logger.info("Adding Support record: %r", support.name)
        support_record = Support(
            support_listing=support_listing,
            name=support.name,
            addresses=support.addresses,
            phone_numbers=support.phone_numbers,
            description=support.description,
            website=support.website,
            email_addresses=support.emails,
        )
        db_session.add(support_record)

    # Update the last_crawled_at timestamp
    job.last_crawled_at = datetime_util.utcnow()
    logger.info("Updated last_crawled_at for domain: %s", job.domain)


def process_crawl_jobs(jobs: list[CrawlJob]) -> list[tuple[CrawlJob, dict[str, SupportEntry]]]:
    """
    Process crawl jobs in parallel using Haystack pipelines.

    Args:
        jobs: List of CrawlJob instances to process

    Returns:
        List of tuples (job, support_entries_dict)
    """
    if not jobs:
        return []

    logger.info(
        "Building pipeline  for %d jobs",
        len(jobs),
    )

    pipeline = build_pipeline()

    # Run pipeline for all jobs in parallel
    logger.info("Processing %d jobs in parallel", len(jobs))
    results = asyncio.run(run_pipeline_and_join_results(pipeline, jobs))

    logger.info("Successfully processed %d jobs", len(results))
    return results


def process_all_jobs(db_session: db.Session) -> None:
    """
    Main processing function that orchestrates the entire crawl job workflow.

    This function:
    1. Fetches all jobs that need processing
    2. Processes them in parallel using Haystack pipelines
    3. Saves results to the database
    """
    jobs = get_jobs_to_process(db_session)

    if not jobs:
        logger.info("No jobs to process")
        return

    # Process jobs in parallel using Haystack pipelines
    results = process_crawl_jobs(jobs)

    # Save results
    for job, support_entries in results:
        logger.info("Saving results for domain: %s", job.domain)
        save_job_results(db_session, job, support_entries.values())

    if len(results) < len(jobs):
        logger.warning(
            "Successfully processed and saved %d out of %d jobs (%d failed)",
            len(results),
            len(jobs),
            len(jobs) - len(results),
        )
    else:
        logger.info("Successfully processed and saved %d jobs", len(results))


def main() -> None:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    with config.db_session() as db_session, db_session.begin():
        process_all_jobs(db_session)
    logger.info("Done")
