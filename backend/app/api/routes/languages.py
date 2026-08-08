from fastapi import APIRouter

from app.core.languages import list_languages
from app.schemas.models import LanguagesResponse

router = APIRouter(prefix="/api/languages", tags=["languages"])


@router.get("", response_model=LanguagesResponse)
def get_languages() -> LanguagesResponse:
    return LanguagesResponse(languages=list_languages())
