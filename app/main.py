from fastapi import FastAPI

from app.api.routes import router as api_router


def create_app() -> FastAPI:
    """Application factory to support future testability and configuration."""
    app = FastAPI(title="Smart Reply Service", version="0.1.0")
    app.include_router(api_router)
    return app


app = create_app()
