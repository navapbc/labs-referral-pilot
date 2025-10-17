import pytest

from src.adapters import db
from src.db.models.support_listing import Support
from tests.src.db.models.factories import SupportFactory, SupportListingFactory


@pytest.fixture
def seed_supports(enable_factory_create, db_session: db.Session):
    # remove all pre-existing Support records
    db_session.query(Support).delete()

    support_listing = SupportListingFactory.create()
    return [SupportFactory.create(support_listing=support_listing) for _ in range(3)]
