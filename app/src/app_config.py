from functools import cached_property

from src.adapters import db
from src.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    # Set HOST to 127.0.0.1 by default to avoid other machines on the network
    # from accessing the application. This is especially important if you are
    # running the application locally on a public network. This needs to be
    # overriden to 0.0.0.0 when running in a container
    host: str = "127.0.0.1"
    port: int = 3000

    phoenix_collector_endpoint: str = "https://phoenix:6006"
    batch_otel: bool = True

    redact_pii: bool = True

    @cached_property
    def db_client(self) -> db.PostgresDBClient:
        return db.PostgresDBClient()

    def db_session(self) -> db.Session:
        return self.db_client.get_session()


config = AppConfig()
