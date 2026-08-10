from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

DESCRIPCION = """
Portal Nacional de Denuncias de Corrupcion.
.

Los endpoints de lectura son publicos y no requieren autenticacion.
Solo escribir o descargar evidencia exige un rol de revisor.
"""

app = FastAPI(
    title="PNDC API",
    version="0.1.0",
    description=DESCRIPCION,
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
def raiz() -> dict[str, str]:
    return {"servicio": "PNDC API", "docs": "/docs"}
