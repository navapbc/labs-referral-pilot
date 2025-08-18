from hayhooks import create_app

# Boot the standard Hayhooks app
hayhooks_app = create_app()


@hayhooks_app.get("/health")
async def health_check():
    return {"status": "ok", "detail": "Hello World!"}
