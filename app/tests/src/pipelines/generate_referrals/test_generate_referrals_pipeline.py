<<<<<<< Updated upstream
import pytest

from src.adapters import db
from src.db.models.support_listing import Support
from src.pipelines.generate_referrals.pipeline_wrapper import format_support_strings
=======
import json

import pytest
from sqlalchemy.inspection import inspect

from src.adapters import db
from src.db.models.support_listing import Support
from src.pipelines.generate_referrals.pipeline_wrapper import retrieve_supports_from_db
>>>>>>> Stashed changes
from tests.src.db.models.factories import SupportFactory, SupportListingFactory


@pytest.fixture
<<<<<<< Updated upstream
def seed_supports(enable_factory_create, db_session: db.Session):
=======
def seed_supports(db_session: db.Session):
>>>>>>> Stashed changes
    # remove all pre-existing Support records
    db_session.query(Support).delete()

    support_listing = SupportListingFactory.create()
<<<<<<< Updated upstream
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
=======
    supports = []
    for i in range(0, 3):
        support = SupportFactory.create(support_listing=support_listing, name=f"support{i}")
        support_as_json_str = json.dumps(
            {c.key: getattr(support, c.key) for c in inspect(Support).mapper.column_attrs},
            default=str,
        )
        supports.append(support_as_json_str)
    return supports


def test_retrieve_supports_from_db(enable_factory_create, seed_supports, db_session: db.Session):
    supports_from_db = retrieve_supports_from_db()

    assert len(supports_from_db) == 3
    assert seed_supports[0] == supports_from_db[0]
    assert seed_supports[1] == supports_from_db[1]
    assert seed_supports[2] == supports_from_db[2]
>>>>>>> Stashed changes
