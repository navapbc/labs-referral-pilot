import argparse
import logging
import os
from pprint import pformat

import httpx
import opentelemetry.exporter.otlp.proto.http.trace_exporter as otel_trace_exporter

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# Arize's Phoenix observability platform
import phoenix.client
import phoenix.otel
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.app_config import config
from src.logging.presidio_pii_filter import PresidioRedactionSpanProcessor

logger = logging.getLogger(__name__)


def _create_client(url=config.phoenix_collector_endpoint, api_key=None) -> phoenix.client.Client:
    logger.info("Creating Phoenix client to %s", url)
    return phoenix.client.Client(base_url=url, api_key=api_key)


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

    if config.redact_pii:
        phoenix_api_key = os.environ.get("PHOENIX_API_KEY")
        span_exporter = otel_trace_exporter.OTLPSpanExporter(
            endpoint=trace_endpoint, headers={"Authorization": f"Bearer {phoenix_api_key}"}
        )
        # Create the PII redacting processor with the OTLP exporter
        pii_processor = PresidioRedactionSpanProcessor(span_exporter)
        # Add the pii processor to the otel instance
        if config.batch_otel:
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        tracer_provider.add_span_processor(pii_processor)


def get_prompt_template(prompt_name, client):
    """Retrieve a prompt template from Phoenix by name.
    https://arize.com/docs/phoenix/sdk-api-reference/python/overview#prompt-management
    """
    prompt_params = which_prompt_version(prompt_name)
    prompt = client.prompts.get(**prompt_params)
    logger.info(
        "Retrieved prompt with %r: id='%s'\n%s", prompt_params, prompt.id, pformat(prompt._dumps())
    )
    return prompt


def which_prompt_version(prompt_name):
    if config.environment == "local":
        # Get the latest version regardless of tags
        return {"prompt_identifier": prompt_name}

    # Use the hardcoded version ids
    return {"prompt_version_id": config.PROMPT_VERSIONS[prompt_name]}


def copy_deployed_prompts():
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("api_key")
    args = parser.parse_args()

    assert args.url
    assert args.api_key
    logger.info("Copying prompts from %s", args.url)
    src_client = _create_client(args.url, api_key=args.api_key)
    for prompt in list_prompts(src_client):
        # The prompt id is base64 encoding of 'Prompt:N' where N is simply a counter
        logger.info("Copying prompt: %r with id=%r)", prompt["name"], prompt["id"])
        copy_prompt(src_client, prompt["name"])


def list_prompts(client):
    "client.prompts doesn't have a list() method, so use the underlying httpx client."
    response = client._client.get("/v1/prompts")
    return response.json()["data"]


def copy_prompt(src_client, prompt_name):
    if prompt_name not in config.PROMPT_VERSIONS:
        logger.warning("No version id found for prompt %r -- skipping", prompt_name)
        return

    prompt_ver = src_client.prompts.get(prompt_version_id=config.PROMPT_VERSIONS[prompt_name])
    logger.info("Retrieved prompt with id='%s'\n%s", prompt_ver.id, pformat(prompt_ver._dumps()))

    local_client = _create_client()
    logger.info("Creating prompt %r in %r", prompt_name, local_client._client.base_url)
    # If prompt_name already exists, a new prompt version will be created
    local_client.prompts.create(
        version=prompt_ver, name=prompt_name, prompt_description=prompt_ver._description
    )
