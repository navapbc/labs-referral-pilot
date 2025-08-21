from src.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    phoenix_collector_endpoint: str = "https://phoenix:6006"
    batch_otel: bool = True


config = AppConfig()
