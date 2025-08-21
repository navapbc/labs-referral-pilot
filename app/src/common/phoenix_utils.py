"""
'make format-check' fails this file even after 'make format'
isort:skip_file
"""
import logging

import httpx

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# Arize's Phoenix observability platform
import phoenix.client
import phoenix.otel

from .app_config import config

logger = logging.getLogger(__name__)


def _create_client() -> phoenix.client.Client:
    logger.info("Creating Phoenix client to %s", config.phoenix_collector_endpoint)
    # If base_url is None, then phoenix.client.Client defaults to PHOENIX_COLLECTOR_ENDPOINT
    # env variable value or "http://localhost:6006"
    return phoenix.client.Client(base_url=config.phoenix_collector_endpoint)


def service_alive() -> bool:
    client = _create_client()
    try:
        projects = client.projects.list()
        logger.info("Phoenix service is alive: %s", projects)
        return True
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as error:
        logger.info("Phoenix service is not alive: %s", error)
    except Exception as error:
        logger.error("Unexpected error when checking Phoenix service: %s", error)
    return False


def configure_phoenix(only_if_alive: bool = True) -> None:
    "Set only_if_alive=True to fail fast if Phoenix is not reachable."
    if only_if_alive and not service_alive():
        raise RuntimeError("Phoenix service is not reachable, cannot configure Phoenix.")

    trace_endpoint = f"{config.phoenix_collector_endpoint}/v1/traces"
    logger.info("Using Phoenix OTEL endpoint: %s", trace_endpoint)

    # Using Phoenix docs: https://arize.com/docs/phoenix/tracing/integrations-tracing/haystack
    logger.info("Using phoenix.otel.register with batch_otel=%s", config.batch_otel)
    # This uses PHOENIX_COLLECTOR_ENDPOINT and PHOENIX_PROJECT_NAME env variables
    # and PHOENIX_API_KEY to handle authentication to Phoenix.
    phoenix.otel.register(
        endpoint=trace_endpoint,
        batch=config.batch_otel,
        # Auto-instrument based on installed OpenInference dependencies
        auto_instrument=True,
    )
