from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TipoInstitucion


class Categoria(Base):
    """tipos de actos denunciados. catalogo cerrado que alimenta el ranking"""

    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<categoria {self.nombre}>"

class Institucion(Base):
    """institucion señalada en una denuncia"""
    __tablename__ = "instituciones"
    id:Mapped[int] =mapped_column(primary_key=True)
    nombre: Mapped[str] =mapped_column(String(160), unique=True, nullable=False)
    tipo: Mapped[TipoInstitucion] = mapped_column(
        SAEnum(
            TipoInstitucion,
            name="tipo_institucion",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,

    )
def __repr__(self) -> str:
    return f"<institucion {self.nombre} ({self.tipo.value})>"
