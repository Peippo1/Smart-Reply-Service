from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routes import router as api_router


def create_app() -> FastAPI:
    """Application factory to support future testability and configuration."""
    app = FastAPI(title="Smart Reply Service", version="0.1.0")

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    app.include_router(api_router)
    return app


app = create_app()
