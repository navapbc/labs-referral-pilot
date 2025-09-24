import pytest

from src.adapters import db
from src.db.models.support_listing import Support
from src.pipelines.generate_referrals.pipeline_wrapper import format_support_strings
from tests.src.db.models.factories import SupportFactory, SupportListingFactory


@pytest.fixture
def seed_supports(enable_factory_create, db_session: db.Session):
    # remove all pre-existing Support records
    db_session.query(Support).delete()

    support_listing = SupportListingFactory.create()
    return [SupportFactory.create(support_listing=support_listing) for _ in range(3)]


def test_format_support_strings(seed_supports):
    support_strings = format_support_strings()

    assert len(support_strings) == len(seed_supports)

    db_supports = {support.id: support for support in seed_supports}
    for k, v in support_strings.items():
        support = db_supports[k]
        # Verify that support data is somewhere in the resulting strings
        assert support.name in v
        assert support.description in v
        for address in support.addresses:
            assert address in v
        for phone_number in support.phone_numbers:
            assert phone_number in v
        assert support.website in v
        for email_address in support.email_addresses:
            assert email_address in v
