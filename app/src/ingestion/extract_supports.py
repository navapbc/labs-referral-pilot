"Add SupportListing and associated Support records to the DB by extracting file contents."

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
from pprint import pformat
from tempfile import NamedTemporaryFile
from typing import Iterable

from haystack import AsyncPipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.dataclasses import Document
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from pydantic import BaseModel, Field
from smart_open import open as smart_open

from src.adapters import db
from src.app_config import config
from src.db.models.support_listing import Support, SupportListing

logger = logging.getLogger(__name__)


def extract_from_pdf(pdf_filepath: str) -> Document:  # pragma: no cover
    if not os.path.exists(pdf_filepath):
        raise FileNotFoundError(f"File not found: {pdf_filepath}")

    # There's also PDFMinerToDocument (for a different pdf extractor) and
    # MultiFileConverter (for variety of file types but requires more dependencies)
    converter = PyPDFToDocument()

    # Since the converter only accept local files,
    # create a temporary file to hold the PDF data in case the file is not local
    with smart_open(pdf_filepath, "rb") as pdf_file:
        # Create temp file
        with NamedTemporaryFile(mode="wb") as tmpfile:
            tmpfile.write(pdf_file.read())
            temp_file = Path(tmpfile.name)

            result = converter.run(sources=[temp_file])
    return result["documents"][0]


def split_doc(doc: Document, passages_per_doc: int = 11, overlap: int = 1) -> list[Document]:
    """
    Split document into multiple documents, each consisting of passages.
    A 'passage' is delimited by '\n\n'
    """
    assert doc.content

    # Remove leading/trailing whitespace from each line so that 'passage' splitting works
    doc.content = "\n".join(line.strip() for line in doc.content.splitlines())

    # Split the document into "passages"
    splitter = DocumentSplitter(
        split_by="passage",
        split_length=passages_per_doc,
        split_overlap=overlap,
    )
    result = splitter.run(documents=[doc])
    return result["documents"]


class SupportEntry(BaseModel):
    name: str
    website: str | None
    emails: list[str]
    addresses: list[str]
    phone_numbers: list[str]
    description: str | None = Field(description="2-sentence summary, including offerings")


SYSTEM_PROMPT_TEMPLATE = f"""Using only the document content provided by the user, return a JSON list of objects.
Each object must match exactly this schema:
```
{json.dumps(SupportEntry.model_json_schema(), indent=2)}
```

Rules:
- Output ONLY raw JSON (no markdown fences, no commentary).
- If a field is missing in the PDF, use null or [] as appropriate.
- Keep strings concise; avoid line breaks inside values.
"""

USER_TEMPLATE = """Document content:
{{ doc.content }}
"""


def create_llm() -> AmazonBedrockChatGenerator:  # pragma: no cover
    # The max_tokens set in Haystack cannot exceed the maximum output token limit supported by the specific model configured on Amazon Bedrock.
    # Anthropic's Claude 3 Sonnet: Newer versions support up to 64k output tokens, but the actual usable limit on
    # Bedrock might differ based on the throughput settings
    return AmazonBedrockChatGenerator(
        model="us.anthropic.claude-3-5-sonnet-20241022-v2:0", generation_kwargs={"max_tokens": 8192}
    )


def build_pipeline() -> AsyncPipeline:
    pipe = AsyncPipeline()

    messages = [
        ChatMessage.from_system(SYSTEM_PROMPT_TEMPLATE),
        ChatMessage.from_user(USER_TEMPLATE),
    ]
    pipe.add_component(
        "prompt_builder", ChatPromptBuilder(template=messages, required_variables="*")
    )
    pipe.add_component("llm", create_llm())
    # If needed, add OutputValidator to retry the LLM call -- https://haystack.deepset.ai/tutorials/28_structured_output_with_loop

    pipe.connect("prompt_builder", "llm")
    return pipe


async def run_pipeline(pipeline: AsyncPipeline, doc: Document) -> list[dict]:
    assert doc.content
    logger.info("Running pipeline with subdoc content length: %d", len(doc.content))

    _result = await pipeline.run_async({"prompt_builder": {"doc": doc}})
    assert len(_result["llm"]["replies"]) == 1
    reply = _result["llm"]["replies"][0]
    # Useful info for checking if tokens have reached the limit for the LLM
    logger.info("Finished pipeline with subdoc content length: %d", len(doc.content))
    logger.debug(pformat(reply.meta))

    support_entries = json.loads(reply.text)
    logger.info("Number of support entries: %d", len(support_entries))
    logger.debug([entry["name"] for entry in support_entries])
    return support_entries


async def run_pipeline_and_join_results(pipeline: AsyncPipeline, docs: list[Document]) -> dict:
    "Run a pipeline for each document in parallel and join the results"
    tasks = [run_pipeline(pipeline, doc) for doc in docs]
    results = await asyncio.gather(*tasks)
    all_results = [item for sublist in results for item in sublist]
    return {entry["name"]: entry for entry in all_results}


def extract_support_entries(name: str, doc: Document) -> dict[str, SupportEntry]:
    # Lengthy document content results in incomplete LLM responses, so split document with some overlap
    # and make multiple calls to the LLM and merge the LLM JSON results, resolving any entries with the same name
    split_docs = split_doc(doc)
    logger.info(
        "Split into %d subdocs with lengths: %s",
        len(split_docs),
        [len(d.content) if d.content else 0 for d in split_docs],
    )

    pipeline = build_pipeline()
    supports = asyncio.run(run_pipeline_and_join_results(pipeline, split_docs))
    logger.info("Total supports: %d", len(supports))
    support_entries = {name: SupportEntry(**data) for name, data in supports.items()}
    return support_entries


def save_to_db(
    db_session: db.Session,
    support_listing: SupportListing,
    support_entries: Iterable[SupportEntry],
) -> None:
    existing_listing = (
        db_session.query(SupportListing)
        .where(SupportListing.name == support_listing.name)
        .one_or_none()
    )
    if existing_listing:
        logger.info("Update existing SupportListing: %r", existing_listing.name)
        existing_listing.uri = support_listing.uri

        logger.info("Deleting Support records associated with: %r", support_listing.name)
        db_session.query(Support).where(Support.support_listing_id == existing_listing.id).delete()
    else:
        logger.info("Adding new SupportListing: %r", support_listing.name)
        db_session.add(support_listing)
        # Flush the session to get the ID populated
        db_session.flush()

    support_listing_id = existing_listing.id if existing_listing else support_listing.id
    assert support_listing_id
    # Populate support records
    for support in support_entries:
        support_record = Support(
            support_listing_id=support_listing_id,
            name=support.name,
            addresses=support.addresses,
            phone_numbers=support.phone_numbers,
            description=support.description,
            website=support.website,
            email_addresses=support.emails,
        )
        db_session.add(support_record)


# To test:
# Download Basic Needs Resource Guide.pdf https://drive.google.com/file/d/1u2LCOoJC7jpPUE6wsQ2ZdiNYaqTb5NzT/view?usp=sharing
# make extract-supports NAME="Basic Needs Resources" FILE=Basic\ Needs\ Resource\ Guide.pdf
def main() -> None:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("filepath")
    args = parser.parse_args()

    doc = extract_from_pdf(args.filepath)
    assert doc.content
    logger.info("Extracted content length: %d", len(doc.content))
    extracted_supports = extract_support_entries(args.name, doc)

    for support in extracted_supports.values():
        logger.info("Support: %r", support.name)

    with config.db_session() as db_session, db_session.begin():
        support_listing = SupportListing(name=args.name, uri=args.filepath)
        save_to_db(db_session, support_listing, extracted_supports.values())

    logger.info("Done")
