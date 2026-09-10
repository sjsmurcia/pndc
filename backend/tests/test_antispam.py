import hashlib
import time

import pytest

from app.services import antispam
from app.services.antispam import (
    CEROS_EXIGIDOS,
    LIMITE_ENVIOS,
    EnvioRechazado,
    emitir_reto,
    honeypot_relleno,
    registrar_envio,
    reiniciar_contador,
    verificar_prueba,
)


def resolver(reto: str) -> str:
    """Hace lo mismo que hara el navegador: buscar por fuerza bruta un
    nonce que produzca un hash con los ceros exigidos."""
    objetivo = "0" * CEROS_EXIGIDOS
    nonce = 0
    while True:
        candidato = str(nonce)
        if hashlib.sha256(f"{reto}{candidato}".encode()).hexdigest().startswith(
            objetivo
        ):
            return candidato
        nonce += 1


@pytest.fixture(autouse=True)
def contador_limpio():
    reiniciar_contador()
    yield
    reiniciar_contador()


# --- Honeypot ---


def test_el_campo_trampa_vacio_pasa():
    assert not honeypot_relleno(None)
    assert not honeypot_relleno("")
    assert not honeypot_relleno("   ")


def test_el_campo_trampa_relleno_delata_al_bot():
    assert honeypot_relleno("https://spam.example")


# --- Prueba de trabajo ---


def test_un_nonce_correcto_pasa():
    reto = emitir_reto()["reto"]
    verificar_prueba(reto, resolver(reto))


def test_un_nonce_cualquiera_no_pasa():
    reto = emitir_reto()["reto"]
    with pytest.raises(EnvioRechazado, match="prueba de trabajo"):
        verificar_prueba(reto, "0")


def test_un_reto_inventado_no_pasa():
    """Sin firma, alguien podria fabricarse un reto trivial."""
    with pytest.raises(EnvioRechazado, match="reto"):
        verificar_prueba("1700000000:aa:bb", "0")


def test_un_reto_manipulado_no_pasa():
    reto = emitir_reto()["reto"]
    emitido, aleatorio, firma = reto.split(":")
    alterado = f"{emitido}:ffffffff{aleatorio[8:]}:{firma}"
    with pytest.raises(EnvioRechazado, match="reto"):
        verificar_prueba(alterado, "0")


def test_un_reto_caducado_no_pasa(monkeypatch):
    reto = emitir_reto()["reto"]
    nonce = resolver(reto)

    # Avanza el reloj mas alla de la vigencia.
    futuro = time.time() + antispam.VIGENCIA_RETO + 10
    monkeypatch.setattr(antispam.time, "time", lambda: futuro)

    with pytest.raises(EnvioRechazado, match="caducado"):
        verificar_prueba(reto, nonce)


def test_dos_retos_seguidos_son_distintos():
    assert emitir_reto()["reto"] != emitir_reto()["reto"]


# --- Rate limit ---


def test_los_envios_dentro_del_limite_pasan():
    for _ in range(LIMITE_ENVIOS):
        registrar_envio()


def test_pasado_el_limite_se_rechaza():
    for _ in range(LIMITE_ENVIOS):
        registrar_envio()
    with pytest.raises(EnvioRechazado, match="demasiados envios"):
        registrar_envio()


def test_la_ventana_se_vacia_con_el_tiempo(monkeypatch):
    for _ in range(LIMITE_ENVIOS):
        registrar_envio()

    futuro = time.time() + antispam.VENTANA_ENVIOS + 1
    monkeypatch.setattr(antispam.time, "time", lambda: futuro)

    registrar_envio()  # no debe lanzar


def test_el_rate_limit_no_guarda_nada_identificable():
    """Solo marcas de tiempo. La firma de registrar_envio no admite IP ni
    identificador alguno, y eso es deliberado."""
    import inspect

    firma = inspect.signature(registrar_envio)
    assert not firma.parameters