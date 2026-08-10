from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["salud"])


class Salud(BaseModel):
    estado: str
    entorno: str


@router.get("/health", response_model=Salud, summary="Estado del servicio")
def health() -> Salud:
    settings = get_settings()
    return Salud(estado="ok", entorno=settings.pndc_env)
