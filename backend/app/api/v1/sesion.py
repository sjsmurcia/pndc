from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencias import COOKIE_SESION, revisor_actual
from app.core.config import get_settings
from app.db.session import get_db
from app.models.revision import Revisor
from app.schemas.revision import Credenciales, RevisorVista
from app.services.autenticacion import (
    DURACION_SESION,
    CredencialesInvalidas,
    autenticar,
    cerrar_sesion,
)

router = APIRouter(prefix="/sesion", tags=["sesion"])


@router.post(
    "",
    response_model=RevisorVista,
    summary="Iniciar sesion como revisor",
)
def iniciar_sesion(
    datos: Credenciales,
    respuesta: Response,
    db: Session = Depends(get_db),
) -> RevisorVista:
    """Abre una sesion y emite la cookie.

    No emite evento a la bitacora: registrar cada inicio de sesion
    permitiria reconstruir los horarios de trabajo de cada revisor, y eso
    excede lo que la rendicion de cuentas exige. Lo que si se registra es
    cada ACCION sobre un caso.
    """
    try:
        revisor, token = autenticar(db, datos.usuario, datos.password)
    except CredencialesInvalidas as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    respuesta.set_cookie(
        key=COOKIE_SESION,
        value=token,
        max_age=int(DURACION_SESION.total_seconds()),
        # httponly: inaccesible desde JavaScript, asi que un XSS no la roba.
        httponly=True,
        # strict: el navegador no la envia en peticiones desde otro sitio,
        # lo que resuelve CSRF sin token adicional.
        samesite="strict",
        # En desarrollo va sobre HTTP; en despliegue, solo HTTPS.
        secure=get_settings().pndc_env != "dev",
        path="/api/v1",
    )

    return RevisorVista(
        id=revisor.id,
        nombre=revisor.nombre,
        organizacion=revisor.organizacion,
        rol=revisor.rol,
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesion",
)
def terminar_sesion(
    respuesta: Response,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> None:
    """Borra la sesion de la base y limpia la cookie."""
    # El token no llega hasta aqui: se borran todas las sesiones de este
    # revisor, que ademas es util si sospecha que le robaron una.
    from sqlalchemy import delete

    from app.models.revision import SesionRevisor

    db.execute(
        delete(SesionRevisor).where(SesionRevisor.revisor_id == revisor.id)
    )
    respuesta.delete_cookie(COOKIE_SESION, path="/api/v1")


@router.get(
    "",
    response_model=RevisorVista,
    summary="Identidad del revisor en sesion",
)
def sesion_actual(revisor: Revisor = Depends(revisor_actual)) -> RevisorVista:
    """Permite al frontend saber si hay sesion y de quien."""
    return RevisorVista(
        id=revisor.id,
        nombre=revisor.nombre,
        organizacion=revisor.organizacion,
        rol=revisor.rol,
    )