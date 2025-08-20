import logging
from pprint import pformat

import httpx

# OpenTelemetry is a common standard for general observability
import opentelemetry.exporter.otlp.proto.http.trace_exporter as otel_trace_exporter
import opentelemetry.sdk.trace as otel_sdk_trace
import opentelemetry.trace

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# Arize's Phoenix observability platform
import phoenix.client
import phoenix.otel

# Arize's OpenInference is a set of conventions that is complimentary to OpenTelemetry
from openinference.instrumentation.haystack import HaystackInstrumentor

from .app_config import config

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)


def create_client() -> phoenix.client.Client:
    logger.info("Creating Phoenix client to %s", config.phoenix_base_url)
    if config.disable_ssl_verification:
        # For other calls (i.e., in Haystack pipelines), something like no_ssl_verification()
        # in haystack_rag.py is needed to disable SSL verification.
        # For local development, we shouldn't enable SSL at all.
        logger.warning("SSL verification is disabled for this call, but not other calls")
        client = httpx.Client(base_url=config.phoenix_base_url, verify=False)
    else:
        client = None

    return phoenix.client.Client(base_url=config.phoenix_base_url, http_client=client)


def service_alive() -> bool:
    client = create_client()
    try:
        projects = client.projects.list()
        logger.info("Phoenix service is alive: %s", projects)
        return True
    except httpx.HTTPStatusError as error:
        logger.info("Phoenix service is not alive: %s", error)
    return False


USE_PHOENIX_OTEL_REGISTER = True
BATCH_OTEL = False


def configure_phoenix(only_if_alive: bool = True) -> None:
    "Set only_if_alive=False to fail fast if Phoenix is not reachable."
    if only_if_alive and not service_alive():
        return

    if opentelemetry.trace._TRACER_PROVIDER:
        logger.info("Opentelemetry tracing already configured; skipping")
        return

    # endpoint = config.phoenix_base_url
    trace_endpoint = f"{config.phoenix_base_url}/v1/traces"
    logger.info("Using Phoenix OTEL endpoint: %s", trace_endpoint)

    # Both implementations produce the same traces
    if USE_PHOENIX_OTEL_REGISTER:
        # Using Phoenix docs: https://arize.com/docs/phoenix/tracing/integrations-tracing/haystack
        logger.info("Using phoenix.otel.register")
        # This uses PHOENIX_COLLECTOR_ENDPOINT and PHOENIX_PROJECT_NAME env variables
        # and PHOENIX_API_KEY to handle authentication to Phoenix.
        phoenix.otel.register(
            endpoint=trace_endpoint,
            batch=BATCH_OTEL,
            # Auto-instrument based on installed OpenInference dependencies
            auto_instrument=True,
        )
    else:
        # Using Haystack docs: https://haystack.deepset.ai/integrations/arize-phoenix
        # This is a more manual setup that uses HaystackInstrumentor
        # Since this doesn't use PHOENIX_PROJECT_NAME, it logs to the 'default' Phoenix project
        logger.info("Using HaystackInstrumentor")
        tracer_provider = otel_sdk_trace.TracerProvider()
        # Set the URL since PHOENIX_COLLECTOR_ENDPOINT is not used by HaystackInstrumentor
        span_exporter = otel_trace_exporter.OTLPSpanExporter(trace_endpoint)
        processor: otel_sdk_trace.export.SpanProcessor
        if BATCH_OTEL:
            processor = otel_sdk_trace.export.BatchSpanProcessor(span_exporter)
        else:
            # Send traces immediately
            processor = otel_sdk_trace.export.SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        # PHOENIX_API_KEY env variable seems to be used by HaystackInstrumentor
        HaystackInstrumentor().instrument(tracer_provider=tracer_provider)


def get_prompt_template(prompt_name: str) -> phoenix.client.types.prompts.PromptVersion:
    # Get the template from Phoenix
    client = create_client()
    # Pull a prompt by name
    prompt = client.prompts.get(prompt_identifier=prompt_name, tag="staging")
    prompt_data = prompt._dumps()
    logger.info("Retrieved prompt: %s", pformat(prompt_data))
    return prompt
