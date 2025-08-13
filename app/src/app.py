import os

import uvicorn
from hayhooks.settings import settings
from hayhooks import create_app


# Explicitly set the path to the pipelines directory
os.environ["HAYHOOKS_PIPELINES_DIR"] = "/src/pipelines"
os.environ["HAYHOOKS_ADDITIONAL_PYTHON_PATH"] = "."
# Boot the standard Hayhooks app
hayhooks_app = create_app()

# Simply append a health check endpoint
@hayhooks_app.get("/health")
async def health_check():
    return {"status": "ok", "detail": "Hello World!"}

if __name__ == "__main__":
    uvicorn.run("app:hayhooks_app", host=settings.host, port=settings.port)
