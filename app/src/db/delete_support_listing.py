"""Delete Support entries and their related SupportListing from the database."""

import argparse
import logging
import sys

from sqlalchemy.orm import Session

from src.app_config import config
from src.db.models.support_listing import Support, SupportListing

logger = logging.getLogger(__name__)


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

    parser = argparse.ArgumentParser(description="Delete a SupportListing entry by name")
    parser.add_argument("name", help="Name of the support listing to delete")

    args = parser.parse_args()

    with config.db_session() as db_session, db_session.begin():
        success = delete_support_listing_by_name(db_session, args.name)

    if not success:
        sys.exit(1)

    logger.info("Done")


if __name__ == "__main__":
    main()
