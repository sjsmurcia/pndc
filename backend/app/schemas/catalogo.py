from pydantic import BaseModel

from app.models.enums import TipoInstitucion


class CategoriaVista(BaseModel):
    id: int
    nombre: str


class InstitucionVista(BaseModel):
    id: int
    nombre: str
    tipo: TipoInstitucion


class Catalogo(BaseModel):
    """Listas que alimentan los desplegables del asistente."""

    categorias: list[CategoriaVista]
    instituciones: list[InstitucionVista]