import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import download, folder, jobs, languages, models, upload, url
from app.config import settings
from app.core.errors import (
    AudioExtractionError,
    FolderNotFoundError,
    InvalidPathError,
    ModelLoadError,
    VideoDownloadError,
)
from app.logging_config import get_logger, log_event, setup_logging

logger = get_logger("scribecast.api")


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
    app.include_router(upload.router)
    app.include_router(folder.router)
    app.include_router(url.router)
    app.include_router(jobs.router)
    app.include_router(download.router)

    @app.exception_handler(FolderNotFoundError)
    @app.exception_handler(InvalidPathError)
    async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
        log_event(logger, "api_bad_request", level=logging.WARNING, path=request.url.path, error=str(exc))
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(AudioExtractionError)
    @app.exception_handler(ModelLoadError)
    @app.exception_handler(VideoDownloadError)
    async def upstream_failure_handler(request: Request, exc: Exception) -> JSONResponse:
        log_event(logger, "api_upstream_failure", level=logging.ERROR, path=request.url.path, error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app


app = create_app()
