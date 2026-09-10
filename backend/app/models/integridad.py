import uuid

from sqlalchemy import CHAR, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, MarcaTiempo


class DescargaEvidencia(Base, MarcaTiempo):
    """Registro de cada copia de evidencia entregada a un revisor.

    Cada descarga produce una copia unica marcada (traitor tracing): si el
    archivo se filtra, marca_id identifica que descarga fue la fuente.
    La justificacion es obligatoria a proposito.
    """

    __tablename__ = "descargas_evidencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidencia_id: Mapped[int] = mapped_column(
        ForeignKey("evidencias.id", ondelete="RESTRICT"), nullable=False
    )
    revisor_id: Mapped[int] = mapped_column(
        ForeignKey("revisores.id", ondelete="RESTRICT"), nullable=False
    )

    justificacion: Mapped[str] = mapped_column(Text, nullable=False)

    # Marca incrustada en la copia entregada. UUID nativo: 16 bytes y
    # validado por el motor, en vez de 36 caracteres de texto.
    marca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )

    # Hash de ESTA copia, distinto del de la evidencia original: la marca
    # cambia los bytes del archivo.
    sha256_copia: Mapped[str] = mapped_column(CHAR(64), nullable=False)

    __table_args__ = (
        Index("ix_descargas_evidencia_id", "evidencia_id"),
        Index("ix_descargas_revisor", "revisor_id"),
    )

    def __repr__(self) -> str:
        return f"<Descarga {self.id} ev{self.evidencia_id}>"


class Bitacora(Base, MarcaTiempo):
    """Registro append-only encadenado por hash.

    Cada evento guarda el hash del anterior: alterar o borrar uno rompe la
    continuidad y el verificador senala el punto exacto de la ruptura.

    El indice es informativo, no una garantia: las secuencias de PostgreSQL
    no son transaccionales y un INSERT revertido deja un hueco. La
    integridad la sostiene la cadena de hashes.
    """

    __tablename__ = "bitacora"

    indice: Mapped[int] = mapped_column(primary_key=True)
    tipo_evento: Mapped[str] = mapped_column(String(60), nullable=False)

    # JSONB y no JSON: se almacena en binario, se indexa y se consulta.
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Nulo solo en el primer evento de la cadena, que no tiene anterior.
    hash_anterior: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    hash_actual: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)

    __table_args__ = (
        Index("ix_bitacora_tipo_evento", "tipo_evento"),
        Index("ix_bitacora_creado", "creado_en"),
    )

    def __repr__(self) -> str:
        return f"<Bitacora {self.indice} {self.tipo_evento}>"
