import logging
import os
from pprint import pformat

import httpx
import opentelemetry.exporter.otlp.proto.http.trace_exporter as otel_trace_exporter
import phoenix.otel
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# Arize's Phoenix observability platform
from phoenix.client import Client
from phoenix.client.types import PromptVersion

from src.app_config import config
from src.logging.presidio_pii_filter import PresidioRedactionSpanProcessor

logger = logging.getLogger(__name__)


def _create_client(
    url: str = config.phoenix_collector_endpoint, api_key: str | None = None
) -> Client:
    logger.info("Creating Phoenix client to %s", url)
    return Client(base_url=url, api_key=api_key)


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


def get_prompt_template(prompt_name: str, prompt_version_id: str = "") -> PromptVersion:
    """Retrieve a prompt template from Phoenix by name.
    https://arize.com/docs/phoenix/sdk-api-reference/python/overview#prompt-management
    """
    if prompt_version_id:
        prompt_params = {"prompt_version_id": prompt_version_id}
    else:
        prompt_params = which_prompt_version(prompt_name)
    client = _create_client()
    prompt = client.prompts.get(**prompt_params)
    logger.info(
        "Retrieved prompt with %r: id='%s'\n%s",
        prompt_params,
        prompt.id,
        pformat(prompt._dumps(), width=160),
    )
    return prompt


def which_prompt_version(prompt_name: str) -> dict:
    if config.environment == "local":
        # Get the latest version regardless of tags
        return {"prompt_identifier": prompt_name}

    # Use the hardcoded version ids
    return {"prompt_version_id": config.PROMPT_VERSIONS[prompt_name]}


def client_to_deployed_phoenix() -> Client:
    url = os.environ.get("DEPLOYED_PHOENIX_URL")
    api_key = os.environ.get("DEPLOYED_PHOENIX_API_KEY")
    logger.info("Creating client to deployed Phoenix at %s with API key: %r", url, api_key)
    assert url, "DEPLOYED_PHOENIX_URL is not set -- add it to override.env"
    assert api_key, "DEPLOYED_PHOENIX_API_KEY is not set -- add it to override.env"
    return _create_client(url, api_key=api_key)


def copy_deployed_prompts() -> None:
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    src_client = client_to_deployed_phoenix()
    local_client = _create_client()
    for prompt in list_prompts(src_client):
        # The prompt id is base64 encoding of 'Prompt:N' where N is simply a counter
        logger.info("Copying prompt: %r with id=%r)", prompt["name"], prompt["id"])
        copy_prompt(src_client, local_client, prompt["name"])


def list_prompts(client: Client) -> list[dict]:
    "client.prompts doesn't have a list() method, so use the underlying httpx client."
    response = client._client.get("/v1/prompts")
    return response.json()["data"]


def copy_prompt(src_client: Client, local_client: Client, prompt_name: str) -> None:
    "Copy a prompt from src_client to local_client"
    if prompt_name not in config.PROMPT_VERSIONS:
        logger.warning("No version id found for prompt %r -- skipping", prompt_name)
        return

    prompt_ver = src_client.prompts.get(prompt_version_id=config.PROMPT_VERSIONS[prompt_name])
    logger.info(
        "Retrieved prompt with id='%s'\n%s", prompt_ver.id, pformat(prompt_ver._dumps(), width=160)
    )

    logger.info("Creating prompt %r in %r", prompt_name, local_client._client.base_url)
    # If prompt_name already exists, a new prompt version will be created
    local_client.prompts.create(
        version=prompt_ver, name=prompt_name, prompt_description=prompt_ver._description
    )


def list_prompt_version_ids(prompt_name: str, client: Client) -> list[str]:
    "List all version ids for a given prompt name. client.prompts doesn't have a list_versions() method."
    response = client._client.get(f"/v1/prompts/{prompt_name}/versions")
    resp_data = response.json()["data"]
    # version tags are not in the response
    return [ver["id"] for ver in resp_data]
    # To get tags for the version: client.prompts.tags.list(prompt_version_id=version_id)
