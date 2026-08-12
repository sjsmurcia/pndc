from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, MarcaTiempo, enum_pg
from app.models.enums import DecisionRevision, RolRevisor


class Revisor(Base):
    # persona designada por la organizacion que opera el portal
    __tablename__ = "revisores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    organizacion: Mapped[str] = mapped_column(String(160), nullable=False)
    rol: Mapped[RolRevisor] = mapped_column(
        enum_pg(RolRevisor, "rol_revisor"),
        nullable=False,
        default=RolRevisor.REVISOR,
    )

    # baja logica un revisor inactivo no recibe asignaciones nuevas
    # las anteriores siguen siendo auditable

    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Revisor {self.nombre} ({self.rol.value})>"


class AsignacionRevision(Base, MarcaTiempo):
    __tablename__ = "asignaciones_revision"

    id: Mapped[int] = mapped_column(primary_key=True)
    denuncia_id: Mapped[int] = mapped_column(
        ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False
    )
    revisor_id: Mapped[int] = mapped_column(
        ForeignKey("revisores.id", ondelete="RESTRICT"), nullable=False
    )
    completada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint(
            "denuncia_id", "revisor_id", name="uq_asignacion_denuncia_revisor"
        ),
        Index("ix_asignaciones_revisor_pendiente", "revisor_id", "completada"),
    )

    def __repr__(self) -> str:
        return f"<Asignacion d{self.denuncia_id} r{self.revisor_id}>"


class Revision(Base, MarcaTiempo):
    """Decision de un revisor sobre una denuncia."""

    __tablename__ = "revisiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    denuncia_id: Mapped[int] = mapped_column(
        ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False
    )
    revisor_id: Mapped[int] = mapped_column(
        ForeignKey("revisores.id", ondelete="RESTRICT"), nullable=False
    )
    decision: Mapped[DecisionRevision] = mapped_column(
        enum_pg(DecisionRevision, "decision_revision"), nullable=False
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_revisiones_denuncia", "denuncia_id"),)

    def __repr__(self) -> str:
        return f"<Revision {self.id} {self.decision.value}>"
