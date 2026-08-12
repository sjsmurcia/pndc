from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, MarcaTiempo


class Publicacion(Base, MarcaTiempo):
    """Version redactada que se publica en el portal.

    No es la denuncia original: es un texto nuevo del que se elimino lo
    que identificaria a terceros no verificados. Nada se publica de forma
    automatica.
    """

    __tablename__ = "publicaciones"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Unica: una denuncia se publica una sola vez. Las correcciones son
    # ediciones de esta fila, no filas nuevas.
    denuncia_id: Mapped[int] = mapped_column(
        ForeignKey("denuncias.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    texto_redactado: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<Publicacion d{self.denuncia_id}>"


class Derivacion(Base, MarcaTiempo):
    """Envio de un caso critico a la autoridad competente.

    Un caso derivado congela su publicacion. La autoridad es ficticia:
    la integracion real esta fuera del alcance del proyecto.
    """

    __tablename__ = "derivaciones"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Sin unique: un mismo caso puede derivarse a mas de una autoridad.
    denuncia_id: Mapped[int] = mapped_column(
        ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False
    )

    autoridad: Mapped[str] = mapped_column(String(160), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_derivaciones_denuncia", "denuncia_id"),
    )

    def __repr__(self) -> str:
        return f"<Derivacion d{self.denuncia_id} -> {self.autoridad}>"