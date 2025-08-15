import os

import uvicorn

from hayhooks.settings import settings
from hayhooks import create_app


# Explicitly set the path to the pipelines directory
# Set the path to the pipelines directory, configurable via environment variable, defaulting to a relative path
os.environ["HAYHOOKS_PIPELINES_DIR"] = os.environ.get(
    "HAYHOOKS_PIPELINES_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../pipelines"))
)
os.environ["HAYHOOKS_ADDITIONAL_PYTHON_PATH"] = "."
# Boot the standard Hayhooks app
hayhooks_app = create_app()


@hayhooks_app.get("/health")
async def health_check():
    return {"status": "ok", "detail": "Hello World!"}


if __name__ == "__main__":
    uvicorn.run("app:hayhooks_app", host=settings.host, port=settings.port)
