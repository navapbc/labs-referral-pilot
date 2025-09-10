from typing import Optional

import faker

import src.adapters.db as db

_postgres_db_session: Optional[db.Session] = None

fake = faker.Faker()


def get_db_session() -> db.Session:
    if _postgres_db_session is None:
        raise Exception()

    return _postgres_db_session
