"""Registro central de modelos.

Alembic importa este paquete con `from app.models import *`. Todo modelo
nuevo debe aparecer aqui, o Base.metadata no lo conocera y las migraciones
autogeneradas saldran vacias.
"""

from app.models.catalogo import Categoria, Institucion
from app.models.denuncia import Denuncia
from app.models.evidencia import Evidencia, Mensaje
from app.models.enums import (
    AutorMensaje,
    EstadoDenuncia,
    Gravedad,
    NivelIdentidad,
    TipoInstitucion,
)

__all__ = [
    "AutorMensaje",
    "Categoria",
    "Denuncia",
    "EstadoDenuncia",
    "Gravedad",
    "Institucion",
    "NivelIdentidad",
    "TipoInstitucion",
]