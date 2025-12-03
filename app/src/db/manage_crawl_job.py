"""Create, update, or delete CrawlJob entries in the database."""

import argparse
import logging

from sqlalchemy.orm import Session

from src.app_config import config
from src.db.delete_support_listing import delete_support_listing_by_name
from src.db.models.crawl_job import CrawlJob
from src.db.models.support_listing import SupportListing

logger = logging.getLogger(__name__)


def upsert_crawl_job(
    db_session: Session, prompt_name: str | None, domain: str, crawling_interval: int
) -> CrawlJob:
    """Create or update a CrawlJob entry.

    Args:
        db_session: Database session
        prompt_name: Name of the prompt to use for this crawl job (optional if using scraper function)
        domain: Domain to crawl
        crawling_interval: Crawling interval in hours (must be positive)

    Returns:
        The created or updated CrawlJob

    Raises:
        ValueError: If crawling_interval is not positive
    """
    if crawling_interval <= 0:
        raise ValueError("crawling_interval must be a positive integer")

    # Check if a CrawlJob with this domain already exists
    existing_job = db_session.query(CrawlJob).where(CrawlJob.domain == domain).one_or_none()

    if existing_job:
        logger.info("Updating existing CrawlJob for domain: %s", domain)
        existing_job.prompt_name = prompt_name
        existing_job.crawling_interval = crawling_interval
        logger.info(
            "Updated CrawlJob (id=%s): prompt_name=%s, domain=%s, crawling_interval=%d",
            existing_job.id,
            existing_job.prompt_name,
            existing_job.domain,
            existing_job.crawling_interval,
        )
        return existing_job
    else:
        logger.info("Creating new CrawlJob for domain: %s", domain)
        new_job = CrawlJob(
            prompt_name=prompt_name,
            domain=domain,
            crawling_interval=crawling_interval,
        )
        db_session.add(new_job)
        db_session.flush()
        logger.info(
            "Created CrawlJob (id=%s): prompt_name=%s, domain=%s, crawling_interval=%d",
            new_job.id,
            new_job.prompt_name,
            new_job.domain,
            new_job.crawling_interval,
        )
        return new_job


def delete_crawl_job(db_session: Session, domain: str) -> bool:
    """Delete a CrawlJob entry by domain name.

    Args:
        db_session: Database session
        domain: Domain of the crawl job to delete

    Returns:
        True if a job was deleted, False if no job was found
    """
    existing_job = db_session.query(CrawlJob).where(CrawlJob.domain == domain).one_or_none()

    if existing_job:
        # Support listings created by crawl job
        support_listing_name = (
            f"Crawl Job: {domain}"  # See first line of save_job_results in process_crawl_jobs.py
        )
        logger.info("Searching for SupportListing named: '%s'", support_listing_name)
        support_listing = (
            db_session.query(SupportListing)
            .where(SupportListing.name == support_listing_name)
            .one_or_none()
        )

        if support_listing:
            delete_support_listing_by_name(db_session, support_listing_name)
            logger.info("Finished deleting SupportListing and dependent support(s) for: %s", support_listing_name)
        else:
            logger.info("No Matching Support Listing was found for domain: %s",  domain)

        logger.info("Deleting CrawlJob (id=%s) for domain: %s", existing_job.id, domain)
        db_session.delete(existing_job)
        logger.info("Deleted CrawlJob for domain: %s", domain)
        return True
    else:
        logger.info("No CrawlJob found for domain: %s", domain)
        return False


def main() -> None:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser(description="Manage CrawlJob entries in the database")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Upsert command
    upsert_parser = subparsers.add_parser("upsert", help="Create or update a CrawlJob entry")
    upsert_parser.add_argument(
        "--prompt-name",
        default=None,
        help="Name of the prompt to use for this crawl job (optional if using scraper function)",
    )
    upsert_parser.add_argument("domain", help="Domain to crawl")
    upsert_parser.add_argument(
        "crawling_interval",
        type=int,
        help="Crawling interval in hours (positive integer)",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a CrawlJob entry by domain")
    delete_parser.add_argument("domain", help="Domain of the crawl job to delete")

    args = parser.parse_args()

    if not args.command:
        parser.error("Please specify a command: upsert or delete")

    with config.db_session() as db_session, db_session.begin():
        if args.command == "upsert":
            try:
                upsert_crawl_job(db_session, args.prompt_name, args.domain, args.crawling_interval)
            except ValueError as e:
                parser.error(str(e))
        elif args.command == "delete":
            delete_crawl_job(db_session, args.domain)

    logger.info("Done")
