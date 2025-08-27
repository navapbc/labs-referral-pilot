import logging
import os

import httpx
import opentelemetry.exporter.otlp.proto.http.trace_exporter as otel_trace_exporter
import opentelemetry.sdk.trace as otel_sdk_trace

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# Arize's Phoenix observability platform
import phoenix.client
import phoenix.otel

from src.app_config import config
from src.logging.presidio_pii_filter import PresidioRedactionSpanProcessor

logger = logging.getLogger(__name__)

redact_pii = os.environ.get("REDACT_PII", "true").lower() == "true"


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
        logger.error("Error connecting to Phoenix service: %s", error)
    except Exception as error:
        logger.error("Unexpected error when checking Phoenix service: %s", error)
    return False


def configure_phoenix(only_if_alive: bool = True) -> None:
    "Set only_if_alive=True to fail fast if Phoenix is not reachable."
    if only_if_alive and not service_alive():
        logger.error(
            "Cannot configure Phoenix service at %s",
            config.phoenix_collector_endpoint,
        )
        return

    trace_endpoint = f"{config.phoenix_collector_endpoint}/v1/traces"
    logger.info("Using Phoenix OTEL endpoint: %s", trace_endpoint)

    # Using Phoenix docs: https://arize.com/docs/phoenix/tracing/integrations-tracing/haystack
    logger.info("Using phoenix.otel.register with batch_otel=%s", config.batch_otel)
    # This uses PHOENIX_COLLECTOR_ENDPOINT and PHOENIX_PROJECT_NAME env variables
    # and PHOENIX_API_KEY to handle authentication to Phoenix.
    tracer_provider = phoenix.otel.register(
        endpoint=trace_endpoint,
        batch=config.batch_otel,
        # Auto-instrument based on installed OpenInference dependencies
        auto_instrument=True,
    )

    if redact_pii:
        span_exporter = otel_trace_exporter.OTLPSpanExporter(trace_endpoint)
        otel_sdk_trace.export.BatchSpanProcessor(span_exporter)
        # Create the PII redacting processor with the OTLP exporter
        pii_processor = PresidioRedactionSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(pii_processor)
