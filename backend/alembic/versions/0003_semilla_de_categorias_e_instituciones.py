"""Semilla de categorias e instituciones

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-11 12:34:12.880732

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, column, table

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATEGORIAS = [
    "Soborno",
    "Desvio de fondos publicos",
    "Uso indebido de recursos del Estado",
    "Licitacion amanada",
    "Trafico de influencias",
    "Enriquecimiento ilicito",
    "Nepotismo",
    "Conflicto de intereses",
    "Abuso de autoridad",
    "Otro",
]

# Instituciones ficticias.
INSTITUCIONES = [
    ("Secretaria de Obras Regionales", "secretaria_estado"),
    ("Secretaria de Salud Territorial", "secretaria_estado"),
    ("Secretaria de Educacion del Valle", "secretaria_estado"),
    ("Instituto de Pensiones del Magisterio", "institucion_descentralizada"),
    ("Instituto de Vivienda Popular", "institucion_descentralizada"),
    ("Comision Reguladora de Agua Potable", "ente_regulador"),
    ("Comision Reguladora de Telecomunicaciones", "ente_regulador"),
    ("Empresa Nacional de Energia Costera", "empresa_publica"),
    ("Portuaria del Litoral", "empresa_publica"),
    ("Municipalidad de San Andres del Valle", "municipalidad"),
    ("Municipalidad de Puerto Lindo", "municipalidad"),
    ("Municipalidad de Villa Esperanza", "municipalidad"),
    ("Juzgado Segundo de lo Contencioso", "poder_judicial"),
    ("Corte Regional de Apelaciones", "poder_judicial"),
    ("Tribunal de Cuentas Regional", "organo_control"),
    ("Fiscalia Especial Anticorrupcion", "organo_control"),
    ("Constructora Vallecrest", "empresa_privada"),
    ("Suministros Medicos del Norte", "empresa_privada"),
    ("Consultores Asociados del Istmo", "empresa_privada"),
]


def upgrade() -> None:
    categorias = table("categorias", column("nombre", String))
    op.bulk_insert(categorias, [{"nombre": n} for n in CATEGORIAS])

    instituciones = table(
        "instituciones",
        column("nombre", String),
        column("tipo", SAEnum(name="tipo_institucion", create_type=False)),
    )
    op.bulk_insert(
        instituciones,
        [{"nombre": n, "tipo": t} for n, t in INSTITUCIONES],
    )


def downgrade() -> None:
    op.execute("DELETE FROM instituciones")
    op.execute("DELETE FROM categorias")