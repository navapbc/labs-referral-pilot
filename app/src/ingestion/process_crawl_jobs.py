"Process scheduled crawl jobs by extracting support resources from domains using OpenAI web search."

import asyncio
import json
import logging
from typing import Iterable

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from src.adapters import db
from src.app_config import config
from src.common import haystack_utils
from src.db.models.crawl_job import CrawlJob
from src.db.models.support_listing import Support, SupportListing
from src.util import datetime_util

logger = logging.getLogger(__name__)


class SupportEntry(BaseModel):
    name: str
    website: str | None
    emails: list[str]
    addresses: list[str]
    phone_numbers: list[str]
    description: str | None = Field(description="2-sentence summary, including offerings")


def get_jobs_to_process(db_session: db.Session) -> list[CrawlJob]:
    """
    Get all crawl jobs that need processing.

    A job needs processing if:
    - last_crawled_at is null (never crawled), OR
    - last_crawled_at is more than crawling_interval hours ago
    """
    now = datetime_util.utcnow()

    jobs = db_session.query(CrawlJob).all()

    jobs_to_process = []
    for job in jobs:
        should_process = False

        if job.last_crawled_at is None:
            logger.info("Job for domain %r has never been crawled", job.domain)
            should_process = True
        else:
            time_since_last_crawl = now - job.last_crawled_at
            hours_since_last_crawl = time_since_last_crawl.total_seconds() / 3600

            if hours_since_last_crawl >= job.crawling_interval:
                logger.info(
                    "Job for domain %r was last crawled %.2f hours ago (interval: %d hours)",
                    job.domain,
                    hours_since_last_crawl,
                    job.crawling_interval,
                )
                should_process = True
            else:
                logger.debug(
                    "Skipping domain %r: last crawled %.2f hours ago (interval: %d hours)",
                    job.domain,
                    hours_since_last_crawl,
                    job.crawling_interval,
                )

        if should_process:
            jobs_to_process.append(job)

    logger.info("Found %d jobs to process", len(jobs_to_process))
    return jobs_to_process


async def call_openai_with_web_search(
    prompt_template: list,
    domain: str,
    schema: dict,
    client: AsyncOpenAI,
) -> list[dict]:
    """
    Call OpenAI API with web_search tool limited to the specified domain.

    Args:
        prompt_template: Phoenix prompt template as list of chat messages
        domain: Domain to restrict web search to
        schema: JSON schema for structured output
        client: AsyncOpenAI client instance

    Returns:
        List of support entries as dictionaries
    """
    # Convert haystack ChatMessage objects to OpenAI format
    messages = []
    for msg in prompt_template:
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        # Replace template variables with actual values
        content = msg.content
        if "{{schema}}" in content:
            content = content.replace("{{schema}}", json.dumps(schema, indent=2))

        messages.append({"role": role, "content": content})

    logger.info("Calling OpenAI API with web_search for domain: %s", domain)
    logger.debug("Messages: %s", messages)

    # Call OpenAI with web_search and o3-mini with high reasoning effort
    # Note: The web_search_options parameter is used to configure web search
    # Type ignore due to evolving OpenAI SDK types for web_search_options
    response = await client.chat.completions.create(  # type: ignore[call-overload]
        model="o3-mini",
        messages=messages,
        web_search_options={"filters": {"domains": [domain]}},
        reasoning_effort="high",
    )

    # Extract the response
    assert len(response.choices) == 1
    message = response.choices[0].message

    logger.info("Received response from OpenAI")
    logger.debug("Response message: %s", message.content)

    # Parse the JSON response
    support_entries = json.loads(message.content)
    logger.info("Parsed %d support entries from response", len(support_entries))

    return support_entries


async def process_single_job(
    job: CrawlJob,
    client: AsyncOpenAI,
) -> tuple[CrawlJob, dict[str, SupportEntry]]:
    """
    Process a single crawl job.

    Args:
        job: CrawlJob instance to process
        client: AsyncOpenAI client instance

    Returns:
        Tuple of (job, dict of support entries keyed by name)
    """
    logger.info("Processing job for domain: %s with prompt: %s", job.domain, job.prompt_name)

    # Get the Phoenix prompt
    prompt_template = haystack_utils.get_phoenix_prompt(job.prompt_name)

    # Define the schema
    schema = SupportEntry.model_json_schema()

    # Call OpenAI API
    support_entries_list = await call_openai_with_web_search(
        prompt_template, job.domain, schema, client
    )

    # Convert to SupportEntry objects and deduplicate by name
    support_entries = {entry["name"]: SupportEntry(**entry) for entry in support_entries_list}

    logger.info(
        "Processed %d unique support entries for domain: %s", len(support_entries), job.domain
    )

    return job, support_entries


async def process_jobs_in_parallel(
    jobs: list[CrawlJob],
    client: AsyncOpenAI,
) -> list[tuple[CrawlJob, dict[str, SupportEntry]]]:
    """
    Process multiple crawl jobs in parallel.

    Args:
        jobs: List of CrawlJob instances to process
        client: AsyncOpenAI client instance

    Returns:
        List of tuples (job, support entries dict)
    """
    tasks = [process_single_job(job, client) for job in jobs]
    results = await asyncio.gather(*tasks)
    return results


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
    existing_listing = (
        db_session.query(SupportListing).where(SupportListing.name == listing_name).one_or_none()
    )

    if existing_listing:
        logger.info("Updating existing SupportListing: %r", listing_name)
        existing_listing.uri = job.domain

        logger.info("Deleting Support records associated with: %r", listing_name)
        db_session.query(Support).where(Support.support_listing_id == existing_listing.id).delete()
        support_listing_id = existing_listing.id
    else:
        logger.info("Creating new SupportListing: %r", listing_name)
        new_listing = SupportListing(name=listing_name, uri=job.domain)
        db_session.add(new_listing)
        # Flush to get the ID
        db_session.flush()
        support_listing_id = new_listing.id

    # Add new Support records
    for support in support_entries:
        logger.info("Adding Support record: %r", support.name)
        support_record = Support(
            support_listing_id=support_listing_id,
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


def process_all_jobs(db_session: db.Session) -> None:
    """
    Main processing function that orchestrates the entire crawl job workflow.

    This function:
    1. Fetches all jobs that need processing
    2. Processes them in parallel using OpenAI
    3. Saves results to the database

    Args:
        client: Optional AsyncOpenAI client. If not provided, one will be created.
    """
    jobs = get_jobs_to_process(db_session)

    if not jobs:
        logger.info("No jobs to process")
        return

    # Process jobs in parallel
    logger.info("Processing %d jobs in parallel", len(jobs))
    results = asyncio.run(process_jobs_in_parallel(jobs, client))

    # Save results
    for job, support_entries in results:
        logger.info("Saving results for domain: %s", job.domain)
        save_job_results(db_session, job, support_entries.values())

    logger.info("Successfully processed %d jobs", len(jobs))


def main() -> None:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    with config.db_session() as db_session, db_session.begin():
        process_all_jobs(db_session)
    logger.info("Done")
