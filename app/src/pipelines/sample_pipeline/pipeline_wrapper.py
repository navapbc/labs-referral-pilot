from hayhooks import BasePipelineWrapper
from haystack import Pipeline


class PipelineWrapper(BasePipelineWrapper):
    name = "sample_pipeline"

    def setup(self) -> None:
        self.pipeline = Pipeline()

    def run_api(self) -> dict:
        return {"ok": True, "message": "sample pipline recognized by Haystack"}
