from functools import cached_property

from src.adapters import db
from src.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    environment: str = "local"
    # Set HOST to 127.0.0.1 by default to avoid other machines on the network
    # from accessing the application. This is especially important if you are
    # running the application locally on a public network. This needs to be
    # overridden to 0.0.0.0 when running in a container
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

    # These versions should only be used for the deployed Phoenix instance.
    # Version ids are base64 encodings of 'PromptVersion:N' where N is simply a counter,
    # so they are not unique across different Phoenix instances.
    PROMPT_VERSIONS: dict = {
        "extract_supports": "UHJvbXB0VmVyc2lvbjozMw==",
        "generate_referrals": "UHJvbXB0VmVyc2lvbjozNw==",
        "generate_action_plan": "UHJvbXB0VmVyc2lvbjozOQ==",
        "crawl_gcta": "UHJvbXB0VmVyc2lvbjozNg==",
        "crawl_indeed": "UHJvbXB0VmVyc2lvbjozNA==",
    }


config = AppConfig()
