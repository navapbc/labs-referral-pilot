import logging
from typing import Dict

from hayhooks import create_app

from src.common import phoenix_utils

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

phoenix_utils.configure_phoenix()

# Boot the standard Hayhooks app
hayhooks_app = create_app()


@hayhooks_app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "detail": "Hello World!"}
