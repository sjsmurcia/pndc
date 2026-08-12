from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

convencion = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convencion)


class MarcaTiempo:
    """Mixin. Solo fecha de creacion: casi nada en este esquema se actualiza."""

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

def enum_pg(tipo, nombre: str)-> SAEnum:
    """nativo de postgres, guarda el valor en minusculas y no el nombre"""
    return SAEnum(
        tipo, 
        name=nombre,
        values_callable=lambda e:[m.value for m in e]


    )