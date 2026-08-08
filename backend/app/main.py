from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import languages, models
from app.config import settings
from app.core.errors import AudioExtractionError, FolderNotFoundError, InvalidPathError, ModelLoadError
from app.logging_config import setup_logging


def create_app() -> FastAPI:
    setup_logging("api")

    app = FastAPI(title="scribe-cast")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(models.router)
    app.include_router(languages.router)

    @app.exception_handler(FolderNotFoundError)
    @app.exception_handler(InvalidPathError)
    async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(AudioExtractionError)
    @app.exception_handler(ModelLoadError)
    async def upstream_failure_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app


app = create_app()
