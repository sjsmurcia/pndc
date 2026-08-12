"""bitacora append-only

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-12 13:10:30.893277

"""
from typing import Sequence, Union

from alembic import op



# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #quitar privilegios al rol de la aplicacion 
    #pndc_app no puede devolverselos otorgar privelegios es potestad del due;o del objeto
    #pndc_owner

    op.execute("REVOKE UPDATE, DELETE ON bitacora FROM pndc_app")

    #reglas del motor, la diferencia con revoke, aqui se aplican a todos los roles
    #incluido el propietario y un superusuario. 
    op.execute(
        "CREATE RULE bitacora_no_update AS ON UPDATE TO bitacora "
        "DO INSTEAD NOTHING"

    )
    op.execute(
        "CREATE RULE bitacora_no_delete AS ON DELETE TO bitacora "
        "DO INSTEAD NOTHING"

    )

def downgrade() -> None:
    op.execute("DROP RULE IF EXISTS bitacora_no_delete ON bitacora")
    op.execute("DROP RULE IF EXISTS bitacora_no_update ON bitacora")
    op.execute("GRANT UPDATE, DELETE ON bitacora TO pndc_app")
