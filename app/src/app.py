import logging
from typing import Dict

from hayhooks import create_app

from src.app_config import config
from src.common import phoenix_utils
from src.ingestion import rag_utils

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

logging.info("Configuring Phoenix...")
phoenix_utils.configure_phoenix()
logging.info("Phoenix configured.")

logging.info("Ingesting into ChromaDB...")
rag_utils.populate_vector_db()
logging.info("ChromaDB populated. Collections: %s", config.chroma_client().list_collections())

# Boot the standard Hayhooks app

logging.info("Starting Hayhooks app...")

hayhooks_app = create_app()

logging.info("Hayhooks app started.")


@hayhooks_app.get("/health")
async def health_check() -> Dict[str, str]:
    logging.info("Health check returning OK.")
    return {"status": "ok", "detail": f"Environment {config.environment} is healthy."}
