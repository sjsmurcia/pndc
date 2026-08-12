"""Registro central de modelos.

Alembic importa este paquete con `from app.models import *`. Todo modelo
nuevo debe aparecer aqui, o Base.metadata no lo conocera y las migraciones
autogeneradas saldran vacias.
"""

from app.models.catalogo import Categoria, Institucion
from app.models.denuncia import Denuncia
from app.models.evidencia import Evidencia, Mensaje
from app.models.revision import AsignacionRevision, Revision, Revisor
from app.models.desenlace import Derivacion, Publicacion
from app.models.integridad import Bitacora, DescargaEvidencia
from app.models.enums import (
    AutorMensaje,
    DecisionRevision,
    EstadoDenuncia,
    Gravedad,
    NivelIdentidad,
    RolRevisor,
    TipoInstitucion,
)

__all__ = [
    "AsignacionRevision",
    "AutorMensaje",
    "Bitacora",
    "Categoria",
    "DescargaEvidencia",
    "DecisionRevision",
    "Denuncia",
    "Derivacion",
    "EstadoDenuncia",
    "Evidencia",
    "Gravedad",
    "Institucion",
    "Mensaje",
    "NivelIdentidad",
    "Revision",
    "Revisor",
    "Publicacion",
    "RolRevisor",
    "TipoInstitucion",
]