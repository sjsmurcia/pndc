"""registro central de modelos.
alembic importa este paquete con 'from app.models import *'
todos los modelos nuevos deben aparecer aqui o base.metada no lo conocera y las migraciones autogeneradas saldran vacias
"""

from app.models.catalogo import Categoria, Institucion
from app.models.enums import TipoInstitucion

__all__ = ["Categoria", "Institucion", "TipoInstitucion"]
