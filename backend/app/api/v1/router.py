from fastapi import APIRouter

from app.api.v1 import catalogo,seguimiento,denuncias,health

from app.api.v1 import catalogo, denuncias, health,revision, seguimiento, sesion


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(catalogo.router)
api_router.include_router(denuncias.router)
api_router.include_router(seguimiento.router)
api_router.include_router(sesion.router)
api_router.include_router(revision.router)



