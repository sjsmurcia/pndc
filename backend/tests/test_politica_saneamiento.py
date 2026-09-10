"""Verificacion de las reglas del saneador.

Estas pruebas no ejercitan logica nueva: comprueban que las decisiones de
diseno siguen en pie. Si alguien decide guardar el original "por si
acaso", o quitar el aislamiento del saneador, aqui se cae.
"""

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"


def compose() -> dict:
    return yaml.safe_load((RAIZ / "docker-compose.yml").read_text(encoding="utf-8"))


# --- SCRUM-45: aislamiento del saneador ---


def test_el_saneador_no_tiene_red():
    """Procesa archivos de origen no confiable con librerias que analizan
    formatos complejos: si un archivo malicioso lo compromete, no debe
    tener por donde salir."""
    servicio = compose()["services"]["sanitizer"]
    assert servicio["network_mode"] == "none"
    assert "networks" not in servicio


def test_el_saneador_no_recibe_credenciales():
    """Sin env_file ni variables: no conoce la base de datos ni el
    almacenamiento."""
    servicio = compose()["services"]["sanitizer"]
    assert "env_file" not in servicio
    assert not servicio.get("environment")


def test_el_saneador_corre_con_privilegios_minimos():
    servicio = compose()["services"]["sanitizer"]
    assert servicio["read_only"] is True
    assert servicio["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in servicio["security_opt"]


def test_el_saneador_solo_comparte_la_cuarentena():
    """Su unico canal con el resto del sistema es un volumen."""
    volumenes = compose()["services"]["sanitizer"]["volumes"]
    assert volumenes == ["quarantine:/var/quarantine"]


# --- SCRUM-46: destruccion del original ---


def test_el_original_no_se_escribe_en_disco():
    """Solo hay una funcion que escriba evidencia, y recibe el resultado
    del saneador, nunca el contenido recibido."""
    fuente = (BACKEND / "app/api/v1/denuncias.py").read_text(encoding="utf-8")

    escrituras = re.findall(r"write_bytes\((\w+)", fuente)
    assert escrituras, "No se encontro ninguna escritura de archivo"
    for variable in escrituras:
        assert variable != "contenido", (
            "Se esta escribiendo el archivo original en disco"
        )


def test_el_original_se_descarta_tras_sanear():
    fuente = (BACKEND / "app/api/v1/denuncias.py").read_text(encoding="utf-8")
    assert "del contenido" in fuente


def test_no_existe_almacenamiento_de_originales():
    """Conservar el original bajo custodia se considero y se descarto: lo
    que puede entregarse, puede exigirse."""
    from app.db.base import Base

    for nombre in Base.metadata.tables:
        assert "original" not in nombre.lower(), nombre


# --- SCRUM-47: advertencia en la interfaz ---


def test_la_respuesta_incluye_el_aviso_de_contenido_visible():
    """El saneamiento elimina lo que el archivo guarda, no lo que muestra.
    Quien envia debe saberlo."""
    from app.schemas.denuncia import EvidenciaSubida

    aviso = EvidenciaSubida.model_fields["aviso"].default
    assert "muestra" in aviso
    assert "guarda" in aviso


def test_el_asistente_advierte_antes_de_adjuntar():
    fuente = (RAIZ / "frontend/src/paginas/Denunciar.tsx").read_text(
        encoding="utf-8"
    )
    assert "Antes de adjuntar un archivo" in fuente
    assert "no se elimina" in fuente