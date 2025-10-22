"""Factories for generating test data.

These factories are used to generate test data for the tests. They are
used both for generating in memory objects and for generating objects
that are persisted to the database.

The factories are based on the `factory_boy` library. See
https://factoryboy.readthedocs.io/en/latest/ for more information.
"""
from datetime import datetime
from typing import Optional

import factory
import factory.fuzzy
import faker
from sqlalchemy.orm import scoped_session

import src.adapters.db as db
import src.db.models.user_models as user_models
import src.util.datetime_util as datetime_util
from src.db.models import crawl_job, support_listing

_db_session: Optional[db.Session] = None

fake = faker.Faker()


def get_db_session() -> db.Session:
    # _db_session is only set in the pytest fixture `enable_factory_create`
    # so that tests do not unintentionally write to the database.
    if _db_session is None:
        raise Exception(
            """Factory db_session is not initialized.

            If your tests don't need to cover database behavior, consider
            calling the `build()` method instead of `create()` on the factory to
            not persist the generated model.

            If running tests that actually need data in the DB, pull in the
            `enable_factory_create` fixture to initialize the db_session.
            """
        )

    return _db_session


# The scopefunc ensures that the session gets cleaned up after each test
# it implicitly calls `remove()` on the session.
# see https://docs.sqlalchemy.org/en/20/orm/contextual.html
Session = scoped_session(lambda: get_db_session(), scopefunc=lambda: get_db_session())


class Generators:
    Now = factory.LazyFunction(datetime.now)
    UtcNow = factory.LazyFunction(datetime_util.utcnow)
    UuidObj = factory.Faker("uuid4", cast_to=None)


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


class RoleFactory(BaseFactory):
    class Meta:
        model = user_models.Role

    user_id = factory.LazyAttribute(lambda u: u.user.id)
    user = factory.SubFactory("tests.src.db.models.factories.UserFactory", roles=[])

    type = factory.Iterator([r.value for r in user_models.RoleType])


class UserFactory(BaseFactory):
    class Meta:
        model = user_models.User

    id = Generators.UuidObj
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = "123-456-7890"
    date_of_birth = factory.Faker("date_object")
    is_active = factory.Faker("boolean")

    roles = factory.RelatedFactoryList(RoleFactory, size=2, factory_related_name="user")


class SupportListingFactory(BaseFactory):
    class Meta:
        model = support_listing.SupportListing

    id = Generators.UuidObj
    name = factory.Faker("name")
    uri = factory.Faker("uri")


class SupportFactory(BaseFactory):
    class Meta:
        model = support_listing.Support

    support_listing = factory.SubFactory(SupportListingFactory)

    name = factory.Faker("name")
    addresses = factory.LazyFunction(lambda: [fake.address().replace("\n", ", ")])
    phone_numbers = factory.LazyFunction(lambda: [fake.phone_number()])
    email_addresses = factory.LazyFunction(lambda: [fake.email()])

    description = factory.LazyFunction(lambda: fake.sentence())
    website = factory.LazyFunction(lambda: fake.url())


class LlmResponseFactory(BaseFactory):
    class Meta:
        model = support_listing.LlmResponse

    id = Generators.UuidObj
    raw_text = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))


class CrawlJobFactory(BaseFactory):
    class Meta:
        model = crawl_job.CrawlJob

    id = Generators.UuidObj
    prompt_name = factory.Faker("word")
    domain = factory.Faker("domain_name")
    crawling_interval = factory.Faker("random_int", min=1, max=168)
