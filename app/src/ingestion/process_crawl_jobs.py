"Process scheduled crawl jobs by extracting support resources from domains using OpenAI web search."

import logging

logger = logging.getLogger(__name__)


def main() -> None:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)
    logger.info("Done")
