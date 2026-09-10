from pydantic import BaseModel, Field

from app.models.enums import RolRevisor
from datetime import datetime
from app.models.enums import EstadoDenuncia, Gravedad, NivelIdentidad

class Credenciales(BaseModel):
    usuario: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=8, max_length=200)


class RevisorVista(BaseModel):
    """Identidad del revisor en sesion. Sin password ni token."""

    id: int
    nombre: str
    organizacion: str
    rol: RolRevisor



class CasoEnCola(BaseModel):
    """vista de la lista"""

    denuncia_id:int
    estado:EstadoDenuncia
    gravedad: Gravedad | None
    categoria:str
    institucion: str
    nivel_identidad: NivelIdentidad
    seudonimo:str | None
    evidencias: int | None
    mensajes_sin_leer:int
    creado_en: datetime
    asignado_a_mi:bool

class EvidenciaEnCaso(BaseModel):
    """metadatos de los archivos adjuntos"""
    evidencia_id:int
    mime:str
    sha256: str
    sanitizada: bool
    creado_en:datetime

class CasoDetalle(BaseModel):
    """Vista completa para el revisor"""
    denuncia_id:int
    estado:EstadoDenuncia
    gravedad: Gravedad | None
    categoria: str
    institucion:str
    nivel_identidad: NivelIdentidad
    seudonimo: str | None
    relato:str
    creado_en: datetime
    evidencias:list[EvidenciaEnCaso]
    mensajes:list["MensajeEnCaso"]
    revisores_asignados:list[str]


class MensajeEnCaso(BaseModel):
    id:int
    autor:str
    cuerpo:str
    creado_en:datetime


