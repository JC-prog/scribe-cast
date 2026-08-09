from fastapi import APIRouter

from app.core.runtime_settings import load_runtime_settings, reset_runtime_settings, save_runtime_settings
from app.schemas.runtime_settings import RuntimeSettingsResponse, RuntimeSettingsUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/settings", response_model=RuntimeSettingsResponse)
def get_settings() -> RuntimeSettingsResponse:
    return RuntimeSettingsResponse.from_settings(load_runtime_settings())


@router.patch("/settings", response_model=RuntimeSettingsResponse)
def update_settings(update: RuntimeSettingsUpdate) -> RuntimeSettingsResponse:
    return RuntimeSettingsResponse.from_settings(save_runtime_settings(update))


@router.post("/settings/reset", response_model=RuntimeSettingsResponse)
def reset_settings() -> RuntimeSettingsResponse:
    return RuntimeSettingsResponse.from_settings(reset_runtime_settings())
