import logging
from typing import Dict

from hayhooks import create_app

from src.common import phoenix_utils

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

logging.info("Configuring Phoenix...")

phoenix_utils.configure_phoenix()

logging.info("Phoenix configured.")

# Boot the standard Hayhooks app

logging.info("Starting Hayhooks app...")

hayhooks_app = create_app()

logging.info("Hayhooks app started.")


@hayhooks_app.get("/health")
async def health_check() -> Dict[str, str]:
    logging.info("Health check returning OK.")
    return {"status": "ok", "detail": "Hello World!"}


@hayhooks_app.get("/sharepoint-updated")
async def sharepoint_updated() -> Dict[str, str]:
    logging.info("Sharepoint updated ping.")
    return {"status": "ok", "detail": "Sharepoint update received."}
