import logging
# from pprint import pformat
# from typing import Optional

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder

from src.common import components, haystack_utils, phoenix_utils
from src.pipelines.generate_referrals.pipeline_wrapper import ResourceList
from src.pipelines.generate_referrals.pipeline_wrapper import PipelineWrapper as OriginalPipelineWrapper

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class PipelineWrapper(OriginalPipelineWrapper):
    name = "generate_referrals_rag"

    def setup(self) -> None:
        pipeline = Pipeline(max_runs_per_component=3)
        pipeline.add_component("load_supports", components.LoadSupports())
        pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                # List all variables (required and optional) that could be used in the prompt template.
                # Don't include "template" as it is implicitly required by ChatPromptBuilder
                variables=[
                    "query",
                    "supports",
                    "response_json",
                    "error_message",
                    "invalid_replies",
                ],
            ),
        )
        pipeline.add_component("llm", components.OpenAIWebSearchGenerator())
        pipeline.add_component("output_validator", components.LlmOutputValidator(ResourceList))
        pipeline.add_component("save_result", components.SaveResult())

        pipeline.connect("load_supports.supports", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("llm.replies", "output_validator")
        pipeline.connect("output_validator.valid_replies", "save_result.replies")

        # Re-trigger the prompt builder with error_message and invalid_replies
        pipeline.connect("output_validator.error_message", "prompt_builder.error_message")
        pipeline.connect("output_validator.invalid_replies", "prompt_builder.invalid_replies")

        pipeline.add_component("logger", components.ReadableLogger())
        pipeline.connect("output_validator.valid_replies", "logger")

        self.pipeline = pipeline


from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack import Pipeline

document_store = ChromaDocumentStore(persist_path="chroma_db")
# from haystack import Document
# document_store.write_documents([
#     Document(content="This is the first document."),
#     Document(content="This is the second document.")
# ])
# Since we didn’t pass any embeddings along with our documents, Chroma will create them using its default embedding function
# print(document_store.count_documents())

def ingest_documents(files: list[str]) -> None:
    """Ingest documents into the vector store."""

    # Create the indexing pipeline
    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component("converter", PyPDFToDocument())
    indexing_pipeline.add_component("splitter", DocumentSplitter(split_length=500, split_overlap=100))
    indexing_pipeline.add_component("embedder", SentenceTransformersDocumentEmbedder(model="multi-qa-mpnet-base-cos-v1"))  # "all-MiniLM-L6-v2"
    indexing_pipeline.add_component("writer", DocumentWriter(document_store=document_store))

    # Connect the components
    indexing_pipeline.connect("converter.documents", "splitter.documents")
    indexing_pipeline.connect("splitter.documents", "embedder.documents")
    indexing_pipeline.connect("embedder.documents", "writer.documents")

    # Run the pipeline to index documents
    indexing_pipeline.run({"converter": {"sources": files}})
