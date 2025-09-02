"Add SupportListing and associated Support records to the DB"

import argparse
import json
import asyncio
import os
import pdb
import sys
from pathlib import Path
from pprint import pprint

# from typing import Any, Dict
from haystack import Pipeline, AsyncPipeline

# from haystack.components.converters import PDFToTextConverter
# from haystack.components.generators import OpenAIChatGenerator
from haystack.components.builders import ChatPromptBuilder, PromptBuilder
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.dataclasses import Document
from haystack.dataclasses.chat_message import ChatMessage
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator

# from haystack.components.converters import PyPDFToDocument
from pydantic import BaseModel, Field


def pdf2doc(pdf_filepath: str) -> Document:
    # There's also PDFMinerToDocument (for a different pdf extractor) and MultiFileConverter (for variety of file types but requires more dependencies)
    converter = PyPDFToDocument()
    result = converter.run(sources=[Path(pdf_filepath)])
    return result["documents"][0]


def split_doc(doc: Document, passages_per_doc: int = 11, overlap: int = 1) -> list[Document]:
    """
    Split document into multiple documents, each consisting of passages.
    A passage is delimited by '\n\n'
    """
    assert doc.content
    # Path(f"{args.name}_document.json").write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")

    # Remove leading/trailing whitespace from each line so that 'passage' splitting works
    lines = [line.strip() for line in doc.content.splitlines()]
    doc.content = "\n".join(lines)

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


SYSTEM_PROMPT_TEMPLATE = f"""
Using only the document content provided by the user, return a JSON list of objects.
Each object must match exactly this schema:
```
{Support.schema_json(indent=2)}
```

Rules:
- Output ONLY raw JSON (no markdown fences, no commentary).
- If a field is missing in the PDF, use null or [] as appropriate.
- Keep strings concise; avoid line breaks inside values.
"""

USER_TEMPLATE = """
Document content:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}
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
    # _doc_content = Path(f"{args.name}_document{i}.json").read_text(encoding="utf-8")
    # json_dict = json.loads(_doc_content)
    # docs = [Document.from_dict(json_dict)]
    docs = [doc]
    assert docs[0].content
    print("subDoc content length:", len(docs[0].content))

        # await asyncio.sleep(10)  # Simulate an I/O-bound operation
        # return [{"name": "Sample Support"}]

    _result = await pipeline.run_async({"prompt_builder": {"documents": docs}})
    # pprint(_result['llm']['replies'])
    assert len(_result["llm"]["replies"]) == 1
    reply = _result["llm"]["replies"][0]
    # Important to check if tokens have reached the limit for the LLM
    pprint(reply.meta)
    support_entries = json.loads(reply.text)
    print("Number of support entries:", len(support_entries))
    print([entry["name"] for entry in support_entries])
    # Path(f"{args.name}_support_entries{i}.json").write_text(json.dumps(support_entries, indent=2), encoding="utf-8")
    return support_entries


async def run_pipeline_and_join_results(docs: list[Document]) -> dict:
    """The main asynchronous function to orchestrate tasks."""
    tasks = [run_pipeline(_pipeline, doc) for doc in docs]
    # Schedule the asynchronous functions to run concurrently
    results = await asyncio.gather(*tasks)
    all_results = [item for sublist in results for item in sublist]
    supports = {entry["name"]: entry for entry in all_results}
    # pdb.set_trace()
    return supports


# Basic Needs Resource Guide.pdf https://drive.google.com/file/d/1u2LCOoJC7jpPUE6wsQ2ZdiNYaqTb5NzT/view?usp=sharing
if __name__ == "__main__":
    print("Adding SupportListing")
    print("Arguments:", sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("filepath")
    args = parser.parse_args()
    print(f"Name: {args.name}, Filepath: {args.filepath}")

    if not os.path.exists(args.filepath):
        raise FileNotFoundError(f"PDF not found: {args.filepath}")

    doc = pdf2doc(args.filepath)
    assert doc.content
    print("Doc content length:", len(doc.content))

    # Lengthy document content results in incomplete LLM responses, so split document with some overlap
    # and make multiple calls to the LLM and merge the LLM JSON results, resolving any entries with the same name
    split_docs = split_doc(doc)
    print(f"Number of split docs: {len(split_docs)}")
    print("Doc lengths:", [len(d.content) if d.content else 0 for d in split_docs])

    # for i, d in enumerate(split_docs):
    #     Path(f"{args.name}_document{i}.json").write_text(json.dumps(d.to_dict(), indent=2), encoding="utf-8")

    _pipeline = build_pipeline()

    path = Path(f"{args.name}_supports.json")
    supports = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(supports, dict):
        supports = {entry["name"]: entry for entry in supports}
    print("Loaded Total supports:", len(supports))

    # TODO: https://docs.haystack.deepset.ai/docs/asyncpipeline
    supports |= asyncio.run(run_pipeline_and_join_results(split_docs[0:4]))
    print("Total supports:", len(supports))
    path.write_text(json.dumps(list(supports.values()), indent=2), encoding="utf-8")

    # 2. Look up the SupportListing by name (unique)
    # 3. Delete existing Support entries and replace with new ones

    print("Done")
