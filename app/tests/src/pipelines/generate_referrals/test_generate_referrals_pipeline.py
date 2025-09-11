import json

import pytest
from sqlalchemy.inspection import inspect

from src.adapters import db
from src.db.models.support_listing import Support
from src.pipelines.generate_referrals.pipeline_wrapper import retrieve_supports_from_db
from tests.src.db.models.factories import SupportFactory, SupportListingFactory


@pytest.fixture
def seed_supports(db_session: db.Session):
    # remove all pre-existing Support records
    db_session.query(Support).delete()

    support_listing = SupportListingFactory.create()
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
