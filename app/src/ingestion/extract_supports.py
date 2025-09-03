"Add SupportListing and associated Support records to the DB"

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
from pprint import pformat

from haystack import AsyncPipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.dataclasses import Document
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator

from pydantic import BaseModel, Field
from smart_open import open as smart_open
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def extract_from_pdf(pdf_filepath: str) -> Document:
    if not os.path.exists(pdf_filepath):
        raise FileNotFoundError(f"File not found: {pdf_filepath}")

    # There's also PDFMinerToDocument (for a different pdf extractor) and
    # MultiFileConverter (for variety of file types but requires more dependencies)
    converter = PyPDFToDocument()

    # Create a temporary file to hold the PDF data for the converter in case the file is not local
    with smart_open(pdf_filepath, "rb") as pdf_file:
        # Create temp file
        with NamedTemporaryFile(mode='wb') as tmpfile:
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


class Support(BaseModel):
    name: str
    urls: list[str]
    emails: list[str]
    addresses: list[str]
    phone_numbers: list[str]
    description: str = Field(description="2-sentence summary, including offerings")


SYSTEM_PROMPT_TEMPLATE = f"""Using only the document content provided by the user, return a JSON list of objects.
Each object must match exactly this schema:
```
{json.dumps(Support.model_json_schema(), indent=2)}
```

Rules:
- Output ONLY raw JSON (no markdown fences, no commentary).
- If a field is missing in the PDF, use null or [] as appropriate.
- Keep strings concise; avoid line breaks inside values.
"""

USER_TEMPLATE = """Document content:
{{ doc.content }}
"""


def build_pipeline() -> AsyncPipeline:
    pipe = AsyncPipeline()

    messages = [
        ChatMessage.from_system(SYSTEM_PROMPT_TEMPLATE),
        ChatMessage.from_user(USER_TEMPLATE),
    ]
    pipe.add_component(
        "prompt_builder", ChatPromptBuilder(template=messages, required_variables="*")
    )

    # The max_tokens set in Haystack cannot exceed the maximum output token limit supported by the specific model configured on Amazon Bedrock.
    # Anthropic's Claude 3 Sonnet: Newer versions support up to 64k output tokens, but the actual usable limit on
    # Bedrock might differ based on the throughput settings.
    # even with a larger context window.
    llm = AmazonBedrockChatGenerator(
        model="us.anthropic.claude-3-5-sonnet-20241022-v2:0", generation_kwargs={"max_tokens": 8192}
    )
    pipe.add_component("llm", llm)
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


def extract_support_entries(name: str, input_file: str) -> dict[str, Support]:
    doc = extract_from_pdf(input_file)
    assert doc.content
    logger.info("Extracted content length: %d", len(doc.content))

    # Lengthy document content results in incomplete LLM responses, so split document with some overlap
    # and make multiple calls to the LLM and merge the LLM JSON results, resolving any entries with the same name
    split_docs = split_doc(doc)
    logger.info(
        "Split into %d subdocs with lengths: %s",
        len(split_docs),
        [len(d.content) if d.content else 0 for d in split_docs],
    )

    supports: dict[str, dict] = {}
    path = Path(f"{name}_supports.json")
    if SAVE_TO_FILE and path.exists():
        loaded_supports = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded_supports, dict):
            supports |= {entry["name"]: entry for entry in loaded_supports}
        logger.info("Loaded %d previous supports", len(supports))
    split_docs = split_docs[:3]

    pipeline = build_pipeline()
    supports |= asyncio.run(run_pipeline_and_join_results(pipeline, split_docs))
    logger.info("Total supports: %d", len(supports))
    if SAVE_TO_FILE:
        path.write_text(json.dumps(list(supports.values()), indent=2), encoding="utf-8")
    support_entries = {name: Support(**data) for name, data in supports.items()}
    return support_entries


# FIXME: temporary
SAVE_TO_FILE = False


# To test:
# Download Basic Needs Resource Guide.pdf https://drive.google.com/file/d/1u2LCOoJC7jpPUE6wsQ2ZdiNYaqTb5NzT/view?usp=sharing
# make extract-supports NAME="Basic Needs Resources" FILE=Basic\ Needs\ Resource\ Guide.pdf
def main() -> None:
    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("filepath")
    args = parser.parse_args()

    extracted_supports = extract_support_entries(args.name, args.filepath)

    # TODO: Look up the SupportListing by name (unique)
    logger.info("Checking for existing SupportListing: %r", args.name)
    # TODO: Delete existing Support entries and replace with new ones
    logger.info("Deleting Support records associated with: %r", args.name)
    # TODO: Populate support records
    for support in extracted_supports.values():
        logger.info("Support: %r", support.name)

    logger.info("Done")
