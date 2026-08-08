from fastapi import APIRouter

from app.core.model_catalog import list_models
from app.schemas.models import ModelsResponse

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelsResponse)
def get_models() -> ModelsResponse:
    return ModelsResponse(models=list_models())
