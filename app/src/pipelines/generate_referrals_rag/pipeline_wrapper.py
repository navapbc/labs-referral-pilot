import logging
from typing import Generator

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever

from src.app_config import config
from src.common import components, haystack_utils
from src.pipelines.generate_referrals.pipeline_wrapper import (
    PipelineWrapper as GenerateReferralsPipelineWrapper,
)
from src.pipelines.generate_referrals.pipeline_wrapper import ResourceList

logger = logging.getLogger(__name__)


class PipelineWrapper(GenerateReferralsPipelineWrapper):
    name = "generate_referrals_rag"

    def _create_pipeline(self) -> Pipeline:
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

        # pipeline.draw(path="generate_referrals_rag.png")
        return pipeline

    def create_pipeline_args(
        self,
        query: str,
        user_email: str,
        *,
        prompt_version_id: str = "",
        suffix: str = "",
        region: str,
        llm_model: str | None = None,
        reasoning_effort: str | None = None,
        streaming: bool = False,
    ) -> dict:
        """Create pipeline run arguments with optional overrides for model, reasoning effort, and streaming."""
        # Get base args from parent class
        base_args = super().create_pipeline_args(
            query,
            user_email,
            prompt_version_id=prompt_version_id,
            suffix=suffix,
            region=region,
            llm_model=llm_model,
            reasoning_effort=reasoning_effort,
            streaming=streaming,
        )

        # Override/add RAG-specific args
        return base_args | {
            # For querying RAG DB
            "query_embedder": {"text": query},
            "retriever": {
                "top_k": config.retrieval_top_k,
                "filters": {"field": "region", "operator": "==", "value": region},
            },
            # Override LLM config for RAG pipeline
            "llm": {
                "model": llm_model or config.generate_referrals_rag_model_version,
                "reasoning_effort": reasoning_effort
                or config.generate_referrals_rag_reasoning_level,
                "streaming": streaming,
            },
        }

    # https://docs.haystack.deepset.ai/docs/hayhooks#openai-compatibility
    # Called for the `{pipeline_name}/chat`, `/chat/completions`, or `/v1/chat/completions` streaming endpoint using Server-Sent Events (SSE)
    def run_chat_completion(self, model: str, messages: list, body: dict) -> Generator:
        # Note: 'model' parameter is the pipeline name, not the LLM model
        assert model == self.name, f"Unexpected model/pipeline name: {model}"

        # Extract custom parameters from the body
        query = body.get("query", "")
        user_email = body.get("user_email", "")

        if not query:
            raise ValueError("query parameter is required")

        if not user_email:
            raise ValueError("user_email parameter is required")

        pipeline_run_args = self.create_pipeline_args(
            query,
            user_email,
            prompt_version_id=body.get("prompt_version_id", ""),
            suffix=body.get("suffix", ""),
            region=body.get("suffix", "centraltx"),
            llm_model=body.get("llm_model", None),
            reasoning_effort=body.get("reasoning_effort", None),
            streaming=True,
        )
        logger.info("Streaming referrals: %s", pipeline_run_args)
        return self.runner.stream_response(
            pipeline_run_args,
            user_id=user_email,
            metadata={"user_id": user_email},
            input_=[query],
            generator_hook=haystack_utils.create_result_id_hook(self.pipeline),
        )
