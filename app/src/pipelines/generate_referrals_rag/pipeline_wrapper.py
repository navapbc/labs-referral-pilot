import logging

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever

from src.app_config import config
from src.common import components, phoenix_utils
from src.pipelines.generate_referrals.pipeline_wrapper import (
    PipelineWrapper as GenerateReferralsPipelineWrapper,
)
from src.pipelines.generate_referrals.pipeline_wrapper import ResourceList

logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class PipelineWrapper(GenerateReferralsPipelineWrapper):
    name = "generate_referrals_rag"

    def setup(self) -> None:
        pipeline = Pipeline(max_runs_per_component=3)

        # Replace LoadSupports() with retrieval from vector DB
        pipeline.add_component(
            "query_embedder", SentenceTransformersTextEmbedder(model=config.rag_embedding_model)
        )
        pipeline.add_component(
            "retriever", ChromaEmbeddingRetriever(config.chroma_document_store())
        )
        pipeline.add_component(
            "output_adapter",
            # https://docs.haystack.deepset.ai/docs/outputadapter
            # Use Jinja template to extract content field from documents and return as list of strings,
            # which is used as input to the prompt builder as supports
            OutputAdapter(
                template="{{ documents | map(attribute='content') | list }}",
                output_type=list,
            ),
        )
        pipeline.connect("query_embedder.embedding", "retriever.query_embedding")
        pipeline.connect("retriever.documents", "output_adapter")

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

        pipeline.connect("output_adapter.output", "prompt_builder.supports")
        pipeline.connect("prompt_builder", "llm.messages")
        pipeline.connect("llm.replies", "output_validator")
        pipeline.connect("output_validator.valid_replies", "save_result.replies")

        # Re-trigger the prompt builder with error_message and invalid_replies
        pipeline.connect("output_validator.error_message", "prompt_builder.error_message")
        pipeline.connect("output_validator.invalid_replies", "prompt_builder.invalid_replies")

        pipeline.add_component("logger", components.ReadableLogger())
        pipeline.connect("output_validator.valid_replies", "logger")

        pipeline.draw(path="generate_referrals_rag.png")
        self.pipeline = pipeline

    def _run_arg_data(self, query: str, user_email: str, prompt_template: str) -> dict:
        top_k = 5
        logger.info("RAG top_k=%d query: %s", top_k, query)
        return super()._run_arg_data(query, user_email, prompt_template) | {
            # For querying RAG DB
            "query_embedder": {"text": query},
            "retriever": {"top_k": top_k, "filters": None},
        }
