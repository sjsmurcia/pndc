from pydantic import BaseModel, Field

from app.models.enums import RolRevisor


class Credenciales(BaseModel):
    usuario: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=8, max_length=200)


class RevisorVista(BaseModel):
    """Identidad del revisor en sesion. Sin password ni token."""

    id: int
    nombre: str
    organizacion: str
    rol: RolRevisor