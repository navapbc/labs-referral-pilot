from src.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    # If set to None, then phoenix.client.Client defaults to PHOENIX_COLLECTOR_ENDPOINT env variable value or "http://localhost:6006"
    phoenix_collector_endpoint: str = "https://phoenix:6006"
    batch_otel: bool = True


config = AppConfig()

print("Using Phoenix endpoint:", config.phoenix_collector_endpoint)
