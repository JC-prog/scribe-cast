from fastapi import APIRouter

from app.config import settings
from app.schemas.version import VersionResponse

router = APIRouter(prefix="/api", tags=["version"])


@router.get("/version", response_model=VersionResponse)
def get_version() -> VersionResponse:
    return VersionResponse(version=settings.app_version)
