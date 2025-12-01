"""Delete Support entries and their related SupportListing from the database."""

import argparse
import logging
import sys

from sqlalchemy.orm import Session

from src.app_config import config
from src.db.models.support_listing import Support, SupportListing

logger = logging.getLogger(__name__)


def delete_support_by_name(db_session: Session, support_name: str) -> bool:
    """Delete a Support entry by name and its related SupportListing if no other supports remain.

    Args:
        db_session: Database session
        support_name: Name of the support to delete

    Returns:
        True if the support was found and deleted, False otherwise
    """
    # Find the support by name
    support = db_session.query(Support).where(Support.name == support_name).one_or_none()

    if not support:
        logger.error("Support with name '%s' not found", support_name)
        return False

    # Get the associated SupportListing before deleting the support
    support_listing_id = support.support_listing_id
    support_listing = support.support_listing

    logger.info("Found Support (id=%s, name='%s')", support.id, support.name)
    logger.info(
        "Associated with SupportListing (id=%s, name='%s')",
        support_listing.id,
        support_listing.name,
    )

    # Delete the support
    db_session.delete(support)
    db_session.flush()
    logger.info("Deleted Support '%s'", support_name)

    # Check if the SupportListing has any remaining supports
    remaining_supports_count = (
        db_session.query(Support).where(Support.support_listing_id == support_listing_id).count()
    )

    if remaining_supports_count == 0:
        logger.info(
            "No remaining supports for SupportListing '%s', deleting it as well",
            support_listing.name,
        )
        db_session.delete(support_listing)
        logger.info("Deleted SupportListing '%s'", support_listing.name)
    else:
        logger.info(
            "SupportListing '%s' has %d remaining support(s), keeping it",
            support_listing.name,
            remaining_supports_count,
        )

    return True


def delete_support_listing_by_name(db_session: Session, listing_name: str) -> bool:
    """Delete a SupportListing entry by name and all its associated Support entries.

    Args:
        db_session: Database session
        listing_name: Name of the support listing to delete

    Returns:
        True if the listing was found and deleted, False otherwise
    """
    # Find the support listing by name
    support_listing = (
        db_session.query(SupportListing).where(SupportListing.name == listing_name).one_or_none()
    )

    if not support_listing:
        logger.error("SupportListing with name '%s' not found", listing_name)
        return False

    # Count associated supports before deletion
    supports_count = (
        db_session.query(Support).where(Support.support_listing_id == support_listing.id).count()
    )

    logger.info("Found SupportListing (id=%s, name='%s')", support_listing.id, support_listing.name)
    logger.info("Associated with %d Support(s)", supports_count)

    # Delete the support listing (will cascade to all associated supports)
    db_session.delete(support_listing)
    db_session.flush()
    logger.info(
        "Deleted SupportListing '%s' and %d associated Support(s)", listing_name, supports_count
    )

    return True


def main() -> None:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser(description="Delete a Support or SupportListing entry by name")
    parser.add_argument("name", help="Name of the support or support listing to delete")
    parser.add_argument(
        "--delete-listing",
        action="store_true",
        help="Delete the entire SupportListing and all associated Supports (instead of a single Support)",
    )

    args = parser.parse_args()

    with config.db_session() as db_session, db_session.begin():
        if args.delete_listing:
            success = delete_support_listing_by_name(db_session, args.name)
        else:
            success = delete_support_by_name(db_session, args.name)

    if not success:
        sys.exit(1)

    logger.info("Done")


if __name__ == "__main__":
    main()
