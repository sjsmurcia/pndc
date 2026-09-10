"""Dependencias de control de acceso.

Se usan con Depends() en cada endpoint del panel de revision. Un endpoint
sin una de estas es un endpoint publico, y eso debe ser una decision
consciente, no un olvido.
"""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import RolRevisor
from app.models.revision import Revisor
from app.services.autenticacion import revisor_de_sesion

COOKIE_SESION = "pndc_sesion"


def revisor_actual(
    sesion: Annotated[str | None, Cookie(alias=COOKIE_SESION)] = None,
    db: Session = Depends(get_db),
) -> Revisor:
    """Exige una sesion valida de revisor.

    La cookie es HttpOnly: no es accesible desde JavaScript, asi que un
    XSS no puede robarla. El coste es que hace falta SameSite=Strict
    contra CSRF, que se configura al emitirla.
    """
    if not sesion:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Se requiere iniciar sesion"
        )

    revisor = revisor_de_sesion(db, sesion)
    if revisor is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Sesion invalida o expirada"
        )

    return revisor


def supervisor_actual(
    revisor: Revisor = Depends(revisor_actual),
) -> Revisor:
    """Exige rol de supervisor.

    Resuelve desacuerdos entre revisores y aprueba casos graves, asi que
    su alcance es mayor y se comprueba aparte.
    """
    if revisor.rol != RolRevisor.SUPERVISOR:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Esta accion requiere rol de supervisor",
        )

    return revisor