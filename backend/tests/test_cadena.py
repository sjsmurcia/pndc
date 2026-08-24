import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.integridad import Bitacora
from app.services.cadena import (
    calcular_hash,
    payload_canonico,
    registrar,
    verificar_cadena,
)
from app.services.eventos import PayloadInvalido, TipoEvento

@compiles(JSONB, "sqlite")
def _jsonb_en_sqlite(tipo, compilador, **kw):
    """JSONB es de PostgreSQL. En SQLite se compila como JSON, que basta
    para probar la logica de la cadena."""
    return "JSON"


@pytest.fixture
def db():
    """SQLite en memoria. Aqui se prueba la logica de encadenamiento, no
    las reglas del motor: esas se verifican contra PostgreSQL."""
    engine = create_engine("sqlite://")
    Bitacora.__table__.create(engine)
    with Session(engine) as sesion:
        yield sesion


def evento_denuncia(n: int = 1) -> dict:
    return {
        "denuncia_id": n,
        "categoria_id": 1,
        "institucion_id": 1,
        "nivel_identidad": "anonimo",
    }


def test_serializacion_es_independiente_del_orden():
    assert payload_canonico({"b": 2, "a": 1}) == payload_canonico(
        {"a": 1, "b": 2}
    )


def test_hash_cambia_si_cambia_el_payload():
    a = calcular_hash("x", {"denuncia_id": 1}, None)
    b = calcular_hash("x", {"denuncia_id": 2}, None)
    assert a != b


def test_primer_evento_no_tiene_anterior(db):
    evento = registrar(db, TipoEvento.DENUNCIA_RECIBIDA, evento_denuncia())
    assert evento.hash_anterior is None
    assert len(evento.hash_actual) == 64


def test_los_eventos_se_encadenan(db):
    primero = registrar(db, TipoEvento.DENUNCIA_RECIBIDA, evento_denuncia(1))
    segundo = registrar(db, TipoEvento.DENUNCIA_RECIBIDA, evento_denuncia(2))
    assert segundo.hash_anterior == primero.hash_actual


def test_cadena_intacta_se_verifica(db):
    for n in range(1, 4):
        registrar(db, TipoEvento.DENUNCIA_RECIBIDA, evento_denuncia(n))
    intacta, indice = verificar_cadena(db)
    assert intacta and indice is None


def test_alterar_un_payload_rompe_la_cadena(db):
    """El caso central: modificar un evento se detecta y se localiza."""
    for n in range(1, 4):
        registrar(db, TipoEvento.DENUNCIA_RECIBIDA, evento_denuncia(n))
    db.flush()

    segundo = db.get(Bitacora, 2)
    segundo.payload = {**segundo.payload, "institucion_id": 99}
    db.flush()

    intacta, indice = verificar_cadena(db)
    assert not intacta
    assert indice == 2


def test_borrar_un_evento_rompe_la_cadena(db):
    """Borrar un eslabon intermedio deja al siguiente apuntando a un hash
    que ya no existe."""
    for n in range(1, 4):
        registrar(db, TipoEvento.DENUNCIA_RECIBIDA, evento_denuncia(n))
    db.flush()

    db.delete(db.get(Bitacora, 2))
    db.flush()

    intacta, indice = verificar_cadena(db)
    assert not intacta
    assert indice == 3


def test_evento_sin_payload_minimo_no_entra(db):
    with pytest.raises(PayloadInvalido):
        registrar(db, TipoEvento.DENUNCIA_RECIBIDA, {"denuncia_id": 1})