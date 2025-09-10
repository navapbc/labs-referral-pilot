from typing import Optional

import src.adapters.db as db

_postgres_db_session: Optional[db.Session] = None


def get_db_session() -> db.Session:
    if _postgres_db_session is None:
        raise Exception("PostgreSQL database session not initialized")

    return _postgres_db_session
