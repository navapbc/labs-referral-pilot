"""Tests for delete_support module."""
import logging

import pytest

from src.db.delete_support import delete_support_by_name
from src.db.models.support_listing import Support, SupportListing
from tests.src.db.models import factories


@pytest.fixture
def caplog_info(caplog):
    """Configure caplog to capture INFO level logs."""
    caplog.set_level(logging.INFO)
    return caplog


"""Tests for delete_support_by_name function."""


def test_delete_single_support_deletes_listing(enable_factory_create, db_session, caplog_info):
    """Test that deleting the only support also deletes the listing."""
    # Create a support listing with a single support
    support_listing = factories.SupportListingFactory.create(name="Test Listing")
    support = factories.SupportFactory.create(name="Test Support", support_listing=support_listing)
    db_session.flush()

    support_id = support.id
    listing_id = support_listing.id

    # Delete the support
    result = delete_support_by_name(db_session, "Test Support")

    assert result is True
    assert "Deleted Support 'Test Support'" in caplog_info.text
    assert "No remaining supports for SupportListing" in caplog_info.text
    assert "Deleted SupportListing 'Test Listing'" in caplog_info.text

    # Verify support and listing are deleted
    assert db_session.query(Support).filter_by(id=support_id).one_or_none() is None
    assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is None


def test_delete_support_keeps_listing_with_remaining_supports(
    enable_factory_create, db_session, caplog_info
):
    """Test that deleting a support keeps the listing if other supports remain."""
    # Create a support listing with multiple supports
    support_listing = factories.SupportListingFactory.create(name="Test Listing 1")
    support1 = factories.SupportFactory.create(
        name="Test Support 1", support_listing=support_listing
    )
    support2 = factories.SupportFactory.create(
        name="Test Support 2", support_listing=support_listing
    )
    db_session.flush()

    support1_id = support1.id
    support2_id = support2.id
    listing_id = support_listing.id

    # Delete one support
    result = delete_support_by_name(db_session, "Test Support 1")

    assert result is True
    assert "Deleted Support 'Test Support 1'" in caplog_info.text
    assert "has 1 remaining support(s), keeping it" in caplog_info.text

    # Verify first support is deleted but listing and second support remain
    assert db_session.query(Support).filter_by(id=support1_id).one_or_none() is None
    assert db_session.query(Support).filter_by(id=support2_id).one_or_none() is not None
    assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is not None


def test_delete_nonexistent_support(enable_factory_create, db_session, caplog_info):
    """Test that deleting a non-existent support returns False."""
    result = delete_support_by_name(db_session, "Nonexistent Support")

    assert result is False
    assert "Support with name 'Nonexistent Support' not found" in caplog_info.text
