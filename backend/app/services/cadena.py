##servicio de cadena de hashes de la bitacora
# cada evento guardara el hash del anterior, formando una cadena ,
# si alguien modifica se rompe la continuidad

# formula
# hash_actual = SHA256(tipo_evento | payload_canonico | hash_anterior)

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integridad import Bitacora
from app.services.eventos import TipoEvento, validar_payload

SEPARADOR = "|"

def payload_canonico(payload: dict) -> str:
    # serializacion reproducible mismo diccionario mismo texto, siempre

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def calcular_hash(
    tipo_evento: str, payload: dict, hash_anterior: str | None
) -> str:
    material = SEPARADOR.join(
        [tipo_evento, payload_canonico(payload), hash_anterior or ""]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def ultimo_evento(db: Session) -> Bitacora | None:
    # ultimo eslabon de la cadena, o none si la bitacora esta vacia
    return db.execute(
        select(Bitacora).order_by(Bitacora.indice.desc()).limit(1)
    ).scalar_one_or_none()


def registrar(db: Session, tipo: TipoEvento, payload: dict) -> Bitacora:
    # agregar un evento a la cadena
    validar_payload(tipo, payload)

    anterior = ultimo_evento(db)
    hash_anterior = anterior.hash_actual if anterior else None

    evento = Bitacora(
        tipo_evento=tipo.value,
        payload=payload,
        hash_anterior=hash_anterior,
        hash_actual=calcular_hash(tipo.value, payload, hash_anterior),
    )
    db.add(evento)
    db.flush()  # asigna indice sin cerrar la transaccion
    return evento


def verificar_cadena(db: Session) -> tuple[bool, int | None]:
    """Recalcula la cadena completa desde el principio.

    Devuelve (True, None) si esta intacta, o (False, indice) senalando el
    primer eslabon que no cuadra.

    Esta es la funcion que la demostracion ejecuta despues de romper la
    base a proposito.
    """
    eventos = db.execute(
        select(Bitacora).order_by(Bitacora.indice.asc())
    ).scalars().all()

    esperado: str | None = None
    for evento in eventos:
        if evento.hash_anterior != esperado:
            return False, evento.indice

        recalculado = calcular_hash(
            evento.tipo_evento, evento.payload, evento.hash_anterior
        )
        if recalculado != evento.hash_actual:
            return False, evento.indice

        esperado = evento.hash_actual

    return True, None