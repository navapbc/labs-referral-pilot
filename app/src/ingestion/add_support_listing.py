"Add SupportListing and associated Support records to the DB"
import argparse
import sys
from pprint import pprint
import pdb

# from haystack.components.converters import PDFToTextConverter
# from haystack.components.generators import OpenAIChatGenerator
from haystack.components.builders import PromptBuilder
from haystack import Pipeline
# from haystack.dataclasses import Document

import json
import os
from typing import Any, Dict

from haystack import Pipeline
from haystack.dataclasses import ByteStream, Document
from haystack.components.converters import PyPDFToDocument, MultiFileConverter
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.builders import PromptBuilder
from haystack.components.builders import ChatPromptBuilder
from haystack_integrations.components.generators.amazon_bedrock import AmazonBedrockChatGenerator
from haystack.dataclasses.chat_message import ChatMessage

from pathlib import Path
# from haystack.components.converters import PyPDFToDocument

def pdf2doc(pdf_filepath: str) -> Document:
    # There's also PDFMinerToDocument (for a different pdf extractor) and MultiFileConverter (for variety of file types but requires more dependencies)
    converter = PyPDFToDocument()
    result = converter.run(sources=[Path(pdf_filepath)])
    return result['documents'][0]


SYSTEM_PROMPT_TEMPLATE = """
Given the document content below, return a JSON list of objects.
Each object must match exactly this schema:
{
  "name": string|null,
  "addresses": string[],
  "phone_numbers": string[],
  "description": string      // 2-sentence summary, including offerings
}

Rules:
- Output ONLY raw JSON (no markdown fences, no commentary).
- If a field is missing in the PDF, use null or [] as appropriate.
- Keep strings concise; avoid line breaks inside values.
"""

USER_TEMPLATE="""
Document content:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}
"""


def build_pipeline() -> Pipeline:
    """
    Create a Haystack v2 pipeline:
      PDF -> text -> split -> prompt -> OpenAI LLM
    """
    pipe = Pipeline()
    # pipe.add_component("pdf_to_text", PyPDFToDocument())  # inputs: sources=[ByteStream]
    # pipe.add_component(
    #     "splitter",
    #     DocumentSplitter(
    #         split_by="word",
    #         split_length=900,
    #         split_overlap=120,
    #         respect_sentence_boundary=True,
    #     ),
    # )
    messages = [
        ChatMessage.from_system(SYSTEM_PROMPT_TEMPLATE),
        ChatMessage.from_user(USER_TEMPLATE),
    ]
    pipe.add_component("prompt_builder", ChatPromptBuilder(template=messages, required_variables="*"))
    pipe.add_component(
        "llm",
        AmazonBedrockChatGenerator(model="us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    )

    # pipe.connect("pdf_to_text.documents", "splitter.documents")
    # pipe.connect("splitter.documents", "prompt_builder.documents")
    pipe.connect("prompt_builder", "llm")
    return pipe


def __summarize_pdf_to_json(pdf_path: str, model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Run the pipeline on a local PDF and return parsed JSON from the LLM.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Load PDF as ByteStream so Haystack's converter can read it
    with open(pdf_path, "rb") as f:
        bs = ByteStream(data=f.read(), meta={"filename": os.path.basename(pdf_path)})

    pipe = build_pipeline(model_name=model_name)

    # Execute the pipeline. Converter expects `sources=[ByteStream(...)]`
    result = pipe.run(
        data={
            "pdf_to_text": {"sources": [bs]},
            # PromptBuilder receives docs via connection; no direct input needed.
            # OpenAIGenerator gets the prompt from PromptBuilder via connection.
        }
    )

    # Haystack OpenAIGenerator returns a list of strings in `replies`
    replies = result["llm"]["replies"]
    if not replies:
        raise RuntimeError("LLM returned no content.")

    raw = replies[0].strip()

    # Be strict: try to parse JSON; if the model hallucinated extra text, attempt a salvage.
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Soft salvage: find first/last braces
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        # If still failing, raise with context
        raise ValueError(f"Model did not return valid JSON. Raw reply was:\n{raw}")


# if __name__ == "__main__":
#     import argparse

#     parser = argparse.ArgumentParser(description="Summarize a PDF to JSON via Haystack + OpenAI.")
#     parser.add_argument("pdf", help="Path to the PDF file")
#     parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name")
#     args = parser.parse_args()

#     summary = __summarize_pdf_to_json(args.pdf, model_name=args.model)
#     print(json.dumps(summary, indent=2, ensure_ascii=False))


def create_pipeline() -> Pipeline:
    # Initialize components
    pdf_converter = PDFToTextConverter()
    prompt_builder = PromptBuilder(template="Extract the key information from the following document: {{documents.content}}")
    llm_generator = AmazonBedrockChatGenerator(model="us.anthropic.claude-3-5-sonnet-20241022-v2:0")

    # Build the pipeline
    pipeline = Pipeline()
    pipeline.add_component("converter", pdf_converter)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", llm_generator)

    # Connect the components
    pipeline.connect("converter.output", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "llm.prompt")
    return pipeline


# Basic Needs Resource Guide.pdf https://drive.google.com/file/d/1u2LCOoJC7jpPUE6wsQ2ZdiNYaqTb5NzT/view?usp=sharing
if __name__ == "__main__":
    print("Adding SupportListing")
    print("Arguments:", sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("filepath")
    args = parser.parse_args()
    print(f"Name: {args.name}, Filepath: {args.filepath}")

    phase = 2
    if phase == 1:
        doc = pdf2doc(args.filepath)
        assert doc.content

        # Save doc to JSON file
        Path(f"{args.name}_document.json").write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")

        doc.content = doc.content[:1000]
        Path(f"{args.name}_document1.json").write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")
    elif phase == 2:
        _pipeline = build_pipeline()

        # _doc_content = Path(f"{args.name}__document1.txt").read_text(encoding="utf-8")
        json_dict = json.loads(Path(f"{args.name}_document1.json").read_text(encoding="utf-8"))
        # TODO: If document exceeds LLM limit, split document with some overlap and make multiple calls to the LLM
        #       Then merge the LLM JSON results, resolving any entries with the same name
        docs = [Document.from_dict(json_dict)]
        _result = _pipeline.run({"prompt_builder": {"documents": docs}})
        # pprint(_result['llm']['replies'])
        assert len(_result['llm']['replies']) == 1
        reply = _result['llm']['replies'][0]
        print(reply.text)
        support_entries = json.loads(reply.text)
        pdb.set_trace()
    else:
        # 1. Read the file contents and extract Support entries using LLM via a Haystack pipeline
        _pipeline = create_pipeline()
        _result = _pipeline.run({"converter": {"sources": [args.filepath]}})
        print(json.dumps(_result, indent=2, ensure_ascii=False))
        print(_result["llm"]["replies"])

    # 2. Look up the SupportListing by name (unique)
    # 3. Delete existing Support entries and replace with new ones

    print("Done")

