from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, MarcaTiempo
from app.models.enums import EstadoDenuncia, Gravedad, NivelIdentidad
def enum_pg(tipo, nombre: str) -> SAEnum:
    """enum nativo de postgres, guarda el valor en minusculas
    y no el nombre del miembro"""
    return SAEnum(tipo, name=nombre, values_callable=lambda e: [m.value for m in e])


class Denuncia(Base, MarcaTiempo):
    """Una denuncia.

    No existe tabla de denunciantes, ni columnas de IP, correo o identidad.
    Del codigo de seguimiento solo se guarda su hash Argon2: si el dato
    nunca se almaceno, nadie puede revelarlo despues.
    """

    __tablename__ = "denuncias"

    id: Mapped[int] = mapped_column(primary_key=True)
    # hash argon2 del codigo de seguimiento. longitud holgada: argon2
    # produce cadenas con parametros y sal incluidos.
    codigo_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False
    )
    institucion_id: Mapped[int] = mapped_column(
        ForeignKey("instituciones.id", ondelete="RESTRICT"), nullable=False
    )
    nivel_identidad: Mapped[NivelIdentidad] = mapped_column(
        enum_pg(NivelIdentidad, "nivel_identidad"),
        nullable=False,
        default=NivelIdentidad.ANONIMO,
    )
    gravedad: Mapped[Gravedad | None] = mapped_column(
        enum_pg(Gravedad, "gravedad"), nullable=True
    )
    estado: Mapped[EstadoDenuncia] = mapped_column(
        enum_pg(EstadoDenuncia, "estado_denuncia"),
        nullable=False,
        default=EstadoDenuncia.RECIBIDA,
    )
    relato: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        Index("ix_denuncias_estado", "estado"),
        Index("ix_denuncias_categoria_institucion",
              "categoria_id", "institucion_id"),
    )

    def __repr__(self)->str:
        return f"<Denuncia {self.id} {self.estado.value}>"