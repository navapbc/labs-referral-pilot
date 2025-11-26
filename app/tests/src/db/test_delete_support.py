"""Tests for delete_support module."""
import logging

import pytest

from src.db.delete_support import delete_support_by_name, delete_support_listing_by_name
from src.db.models.support_listing import Support, SupportListing
from tests.src.db.models import factories


@pytest.fixture
def caplog_info(caplog):
    """Configure caplog to capture INFO level logs."""
    caplog.set_level(logging.INFO)
    return caplog


class TestDeleteSupportByName:
    """Tests for delete_support_by_name function."""

    def test_delete_single_support_deletes_listing(
        self, enable_factory_create, db_session, caplog_info
    ):
        """Test that deleting the only support also deletes the listing."""
        # Create a support listing with a single support
        support_listing = factories.SupportListingFactory.create(name="Test Listing")
        support = factories.SupportFactory.create(
            name="Test Support", support_listing=support_listing
        )
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
        self, enable_factory_create, db_session, caplog_info
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

    def test_delete_nonexistent_support(self, enable_factory_create, db_session, caplog_info):
        """Test that deleting a non-existent support returns False."""
        result = delete_support_by_name(db_session, "Nonexistent Support")

        assert result is False
        assert "ERROR: Support with name 'Nonexistent Support' not found" in caplog_info.text

    def test_delete_support_with_multiple_supports_in_listing(
        self, enable_factory_create, db_session, caplog_info
    ):
        """Test deleting supports one by one until listing is also deleted."""
        # Create a support listing with three supports
        support_listing = factories.SupportListingFactory.create(name="Multi Support Listing")
        factories.SupportFactory.create(
            name="Support 1", support_listing=support_listing
        )
        factories.SupportFactory.create(
            name="Support 2", support_listing=support_listing
        )
        factories.SupportFactory.create(
            name="Support 3", support_listing=support_listing
        )
        db_session.flush()

        listing_id = support_listing.id

        # Delete first support
        delete_support_by_name(db_session, "Support 1")
        assert "has 2 remaining support(s)" in caplog_info.text
        assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is not None

        # Delete second support
        caplog_info.clear()
        delete_support_by_name(db_session, "Support 2")
        assert "has 1 remaining support(s)" in caplog_info.text
        assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is not None

        # Delete third support (last one, should delete listing)
        caplog_info.clear()
        delete_support_by_name(db_session, "Support 3")
        assert "No remaining supports for SupportListing" in caplog_info.text
        assert "Deleted SupportListing 'Multi Support Listing'" in caplog_info.text
        assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is None


class TestDeleteSupportListingByName:
    """Tests for delete_support_listing_by_name function."""

    def test_delete_listing_with_multiple_supports(
        self, enable_factory_create, db_session, caplog_info
    ):
        """Test that deleting a listing also deletes all associated supports."""
        # Create a support listing with multiple supports
        support_listing = factories.SupportListingFactory.create(name="Test Listing 2")
        support1 = factories.SupportFactory.create(
            name="Support 1", support_listing=support_listing
        )
        support2 = factories.SupportFactory.create(
            name="Support 2", support_listing=support_listing
        )
        support3 = factories.SupportFactory.create(
            name="Support 3", support_listing=support_listing
        )
        db_session.flush()

        support1_id = support1.id
        support2_id = support2.id
        support3_id = support3.id
        listing_id = support_listing.id

        # Delete the listing
        result = delete_support_listing_by_name(db_session, "Test Listing 2")

        assert result is True
        assert "Associated with 3 Support(s)" in caplog_info.text
        assert (
            "Deleted SupportListing 'Test Listing 2' and 3 associated Support(s)" in caplog_info.text
        )

        # Verify listing and all supports are deleted
        assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is None
        assert db_session.query(Support).filter_by(id=support1_id).one_or_none() is None
        assert db_session.query(Support).filter_by(id=support2_id).one_or_none() is None
        assert db_session.query(Support).filter_by(id=support3_id).one_or_none() is None

    def test_delete_listing_with_single_support(
        self, enable_factory_create, db_session, caplog_info
    ):
        """Test that deleting a listing with a single support works correctly."""
        # Create a support listing with a single support
        support_listing = factories.SupportListingFactory.create(name="Single Support Listing")
        support = factories.SupportFactory.create(
            name="Only Support", support_listing=support_listing
        )
        db_session.flush()

        support_id = support.id
        listing_id = support_listing.id

        # Delete the listing
        result = delete_support_listing_by_name(db_session, "Single Support Listing")

        assert result is True
        assert "Associated with 1 Support(s)" in caplog_info.text
        assert (
            "Deleted SupportListing 'Single Support Listing' and 1 associated Support(s)"
            in caplog_info.text
        )

        # Verify listing and support are deleted
        assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is None
        assert db_session.query(Support).filter_by(id=support_id).one_or_none() is None

    def test_delete_listing_with_no_supports(self, enable_factory_create, db_session, caplog_info):
        """Test that deleting a listing with no supports works correctly."""
        # Create a support listing with no supports
        support_listing = factories.SupportListingFactory.create(name="Empty Listing")
        db_session.flush()

        listing_id = support_listing.id

        # Delete the listing
        result = delete_support_listing_by_name(db_session, "Empty Listing")

        assert result is True
        assert "Associated with 0 Support(s)" in caplog_info.text
        assert (
            "Deleted SupportListing 'Empty Listing' and 0 associated Support(s)" in caplog_info.text
        )

        # Verify listing is deleted
        assert db_session.query(SupportListing).filter_by(id=listing_id).one_or_none() is None

    def test_delete_nonexistent_listing(self, enable_factory_create, db_session, caplog_info):
        """Test that deleting a non-existent listing returns False."""
        result = delete_support_listing_by_name(db_session, "Nonexistent Listing")

        assert result is False
        assert "ERROR: SupportListing with name 'Nonexistent Listing' not found" in caplog_info.text

    def test_delete_listing_does_not_affect_other_listings(
        self, enable_factory_create, db_session, caplog_info
    ):
        """Test that deleting a listing doesn't affect other listings."""
        # Create two separate support listings
        listing1 = factories.SupportListingFactory.create(name="Listing 1")
        factories.SupportFactory.create(name="Support 1A", support_listing=listing1)
        factories.SupportFactory.create(name="Support 1B", support_listing=listing1)

        listing2 = factories.SupportListingFactory.create(name="Listing 2")
        support2a = factories.SupportFactory.create(name="Support 2A", support_listing=listing2)
        support2b = factories.SupportFactory.create(name="Support 2B", support_listing=listing2)

        db_session.flush()

        listing2_id = listing2.id
        support2a_id = support2a.id
        support2b_id = support2b.id

        # Delete the first listing
        result = delete_support_listing_by_name(db_session, "Listing 1")

        assert result is True
        assert "Deleted SupportListing 'Listing 1' and 2 associated Support(s)" in caplog_info.text

        # Verify second listing and its supports are still present
        assert db_session.query(SupportListing).filter_by(id=listing2_id).one_or_none() is not None
        assert db_session.query(Support).filter_by(id=support2a_id).one_or_none() is not None
        assert db_session.query(Support).filter_by(id=support2b_id).one_or_none() is not None
