from sqlalchemy import Boolean, CHAR, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, MarcaTiempo, enum_pg
from app.models.enums import AutorMensaje


class Evidencia(Base, MarcaTiempo):
    """Archivo adjunto ya saneado.

    Solo se guarda la version publicable: el original se destruye tras
    sanear, porque conservarlo seria mantener un archivo con GPS a la
    espera de filtrarse.
    """

    __tablename__ = "evidencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    denuncia_id: Mapped[int] = mapped_column(
        ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False
    )

    url: Mapped[str] = mapped_column(String(500), nullable=False)

    # SHA-256 en hexadecimal: siempre 64 caracteres. CHAR fijo en vez de
    # VARCHAR porque la longitud no varia nunca.
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)

    mime: Mapped[str] = mapped_column(String(120), nullable=False)

    # Falso mientras el archivo sigue en cuarentena. Solo se publica lo
    # que llego a verdadero.
    sanitizada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (Index("ix_evidencias_denuncia", "denuncia_id"),)

    def __repr__(self) -> str:
        return f"<Evidencia {self.id} {self.mime}>"


class Mensaje(Base, MarcaTiempo):
    """Hilo de dialogo entre quien denuncia y el revisor.

    El denunciante escribe autenticandose con su codigo de seguimiento,
    no con una cuenta. Por eso autor guarda el lado del dialogo y no una
    identidad.
    """

    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(primary_key=True)
    denuncia_id: Mapped[int] = mapped_column(
        ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False
    )
    autor: Mapped[AutorMensaje] = mapped_column(
        enum_pg(AutorMensaje, "autor_mensaje"), nullable=False
    )
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_mensajes_denuncia_creado", "denuncia_id", "creado_en"),
    )

    def __repr__(self) -> str:
        return f"<Mensaje {self.id} de {self.autor.value}>"