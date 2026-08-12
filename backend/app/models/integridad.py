import uuid
from sqlalchemy import CHAR, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


from app.db.base import Base, MarcaTiempo


class DescargaEvidencia(Base, MarcaTiempo):
    # registro de cada copia de la evidencia entrega a los supervisores

    __tablename__ = "descargas_evidencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidencia_id: Mapped[int] = mapped_column(
        ForeignKey("revisores.id", ondelete="RESTRICT"), nullable=False
    )
    revisor_id: Mapped[int] = mapped_column(
        ForeignKey("revisores.id", ondelete="RESTRICT"), nullable=False
    )

    justificacion: Mapped[str] = mapped_column(Text, nullable=False)


# marca incrustada en la copia entregada.
# uuid nativo pgsql 16 bytes y validado por el motor
marca_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    unique=True,
    nullable=False,
    default=uuid.uuid4,
)

# has de esta copia, distinto del de la evidencia original

sha256_copia: Mapped[str] = mapped_column(CHAR(64), nullable=False)

__table_args__ = (
    Index("ix_descargas_evidencia_Id", "evidencia_id"),
    Index("ix_descargas_revisor", "revisor_id"),
)


def __repr__(self) -> str:
    return f"<Descarga {self} ev{self.evidencia_id}>"


class Bitacora(Base, MarcaTiempo):
    # registro append-only encadenado por hash

    __tablename__ = "bitacora"

    indice: Mapped[int] = mapped_column(primary_key=True)
    tipo_evento: Mapped[str] = mapped_column(String(60), nullable=False)

    # jsonb y no json se almacena en binario se indexa x consulta
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # nulo solo en el primer evento de la cadena
    hash_anterior: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    hash_actual: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)
    __table_args__ = (
        Index("ix_bitacora_tipo_evento", "tipo_evento"),
        Index("ix_bitacora_creado", "creado_en"),
    )

    def __repr__(self) -> str:
        return f"<Bitacora {self.indice} {self.tipo_evento}>"
