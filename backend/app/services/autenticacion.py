"""autenticacion de revisores"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.revision import Revisor, SesionRevisor

DURACION_SESION = timedelta(hours=8)

_hasher = PasswordHasher()


class CredencialesInvalidas(Exception):
    """Usuario o contrasena incorrectos, o cuenta inactiva."""


def hashear_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _hash_token(token: str) -> str:
    """SHA-256 basta aqui, a diferencia del codigo de seguimiento.

    El token ya son 256 bits aleatorios: no hay nada que adivinar por
    fuerza bruta, asi que no hace falta un hash lento como Argon2.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def autenticar(db: Session, usuario: str, password: str) -> tuple[Revisor, str]:
    """Valida credenciales y abre una sesion.

    Devuelve el revisor y el token en claro. El token solo existe en esta
    respuesta: en la base queda su hash.
    """
    revisor = db.execute(
        select(Revisor).where(Revisor.usuario == usuario)
    ).scalar_one_or_none()

    # Mismo error para usuario inexistente, contrasena mala y cuenta
    # inactiva: distinguirlos permitiria averiguar que usuarios existen.
    if revisor is None or not verificar_password(password, revisor.password_hash):
        raise CredencialesInvalidas("Usuario o contrasena incorrectos")

    if not revisor.activo:
        raise CredencialesInvalidas("Usuario o contrasena incorrectos")

    token = secrets.token_urlsafe(32)

    db.add(
        SesionRevisor(
            revisor_id=revisor.id,
            token_hash=_hash_token(token),
            expira_en=datetime.now(timezone.utc) + DURACION_SESION,
        )
    )
    db.flush()

    return revisor, token


def revisor_de_sesion(db: Session, token: str) -> Revisor | None:
    """Devuelve el revisor de una sesion valida, o None.

    Comprueba tambien que la cuenta siga activa: dar de baja a un revisor
    corta su acceso en la siguiente peticion, sin esperar a que expire.
    """
    sesion = db.execute(
        select(SesionRevisor).where(SesionRevisor.token_hash == _hash_token(token))
    ).scalar_one_or_none()

    if sesion is None:
        return None

    if sesion.expira_en <= datetime.now(timezone.utc):
        return None

    revisor = db.get(Revisor, sesion.revisor_id)
    if revisor is None or not revisor.activo:
        return None

    return revisor


def cerrar_sesion(db: Session, token: str) -> None:
    """Borra la sesion. El acceso muere de inmediato."""
    db.execute(
        delete(SesionRevisor).where(SesionRevisor.token_hash == _hash_token(token))
    )


def purgar_sesiones_expiradas(db: Session) -> int:
    """Limpieza. Las sesiones expiradas ya no sirven pero ocupan sitio."""
    resultado = db.execute(
        delete(SesionRevisor).where(
            SesionRevisor.expira_en <= datetime.now(timezone.utc)
        )
    )
    return resultado.rowcount or 0
