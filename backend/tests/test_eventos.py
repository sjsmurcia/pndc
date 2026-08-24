import pytest

from app.services.eventos import (
    CLAVES_PROHIBIDAS,
    PAYLOAD_MINIMO,
    PayloadInvalido,
    TipoEvento,
    validar_payload,
)


def test_todo_evento_tiene_contrato():
    """Un evento sin payload minimo definido entraria sin validar."""
    assert set(PAYLOAD_MINIMO) == set(TipoEvento)


def test_eventos_de_revisor_llevan_revisor_id():
    """Quien revisa responde por todo: sus eventos siempre lo identifican."""
    de_revisor = {
        TipoEvento.REVISOR_ASIGNADO,
        TipoEvento.GRAVEDAD_ASIGNADA,
        TipoEvento.REVISION_EMITIDA,
        TipoEvento.CASO_ESCALADO,
        TipoEvento.CASO_DERIVADO,
        TipoEvento.CASO_PUBLICADO,
        TipoEvento.CASO_RECHAZADO,
        TipoEvento.EVIDENCIA_DESCARGADA,
        TipoEvento.HILO_CERRADO_POR_REVISOR,
    }
    for tipo in de_revisor:
        assert "revisor_id" in PAYLOAD_MINIMO[tipo], tipo.value


def test_eventos_de_denunciante_no_llevan_identidad():
    """Quien denuncia no arriesga nada: sus eventos no identifican a nadie."""
    de_denunciante = {
        TipoEvento.DENUNCIA_RECIBIDA,
        TipoEvento.EVIDENCIA_RECIBIDA,
        TipoEvento.MENSAJE_AGREGADO,
    }
    for tipo in de_denunciante:
        claves = set(PAYLOAD_MINIMO[tipo])
        assert not claves & CLAVES_PROHIBIDAS, tipo.value
        assert "revisor_id" not in claves, tipo.value


def test_payload_valido_pasa():
    validar_payload(
        TipoEvento.DENUNCIA_RECIBIDA,
        {
            "denuncia_id": 1,
            "categoria_id": 2,
            "institucion_id": 3,
            "nivel_identidad": "anonimo",
        },
    )


def test_payload_incompleto_falla():
    with pytest.raises(PayloadInvalido, match="faltan"):
        validar_payload(TipoEvento.DENUNCIA_RECIBIDA, {"denuncia_id": 1})


def test_payload_con_clave_prohibida_falla():
    """El caso que de verdad importa: nada que identifique entra al registro."""
    with pytest.raises(PayloadInvalido, match="prohibidas"):
        validar_payload(
            TipoEvento.DENUNCIA_RECIBIDA,
            {
                "denuncia_id": 1,
                "categoria_id": 2,
                "institucion_id": 3,
                "nivel_identidad": "anonimo",
                "codigo_hash": "$argon2id$...",
            },
        )