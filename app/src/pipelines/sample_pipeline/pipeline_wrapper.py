from haystack import Pipeline
from hayhooks import BasePipelineWrapper
from pathlib import Path

class PipelineWrapper(BasePipelineWrapper):
    """
    A generic health-check pipeline for Hayhooks.
    POST /sample_pipeline/run with {"text": "..."} to get an echo back.
    """

    name = "sample_pipeline"

    def setup(self) -> None:
        # Load and build the Haystack pipeline from YAML
        pipeline_yaml = (Path(__file__).parent / "pipeline.yml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)

    def run_api(self, text: str = "ping") -> dict:
        """
        Echo the 'text' you send.
        """
        result = self.pipeline.run({"prompt_builder": {"text": text}})
        prompt = result["prompt_builder"]["prompt"]
        # PromptBuilder returns a string (or list of strings in some contexts)
        echoed = prompt[0] if isinstance(prompt, list) else prompt
        return {"ok": True, "message": echoed}
