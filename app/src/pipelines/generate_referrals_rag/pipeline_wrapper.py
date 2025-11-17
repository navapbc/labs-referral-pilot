import logging

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder

from src.common import components, haystack_utils, phoenix_utils
from src.pipelines.generate_referrals.pipeline_wrapper import (
    PipelineWrapper as OriginalPipelineWrapper,
)
from src.pipelines.generate_referrals.pipeline_wrapper import ResourceList
from src.pipelines.generate_referrals_rag import direct

# from pprint import pformat
# from typing import Optional


logger = logging.getLogger(__name__)
tracer = phoenix_utils.tracer_provider.get_tracer(__name__)


class PipelineWrapper(OriginalPipelineWrapper):
    name = "generate_referrals_rag"

    def setup(self) -> None:
        direct.populate_vector_db()

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

