"""semilla de revisores

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-10 09:33:36.690591

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from argon2 import PasswordHasher
from sqlalchemy import Boolean,String, Column, table
from sqlalchemy import Enum as SAEnum
_hasher = PasswordHasher()

REVISORES = [
    ("ana.reyes", "revisor123", "Ana Reyes", "Observatorio Ciudadano", "revisor"),
    ("luis.mora", "revisor123", "Luis Mora", "Observatorio Ciudadano", "revisor"),
    ("marta.solis", "supervisor123", "Marta Solis", "Observatorio Ciudadano", "supervisor"),
]


# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    revisores = table(
        "revisores",
        Column("usuario", String),
        Column("password_hash", String),
        Column("nombre", String),
        Column("organizacion", String),
        Column("rol", SAEnum(name="rol_revisor", create_type=False)),
        Column("activo", Boolean),
    )

    op.bulk_insert(
        revisores,
        [
            {
                "usuario": usuario,
                "password_hash": _hasher.hash(password),
                "nombre": nombre,
                "organizacion": organizacion,
                "rol": rol,
                "activo": True
            }
            for usuario, password, nombre, organizacion, rol in REVISORES
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM revisores")
