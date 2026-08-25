"""Auditoria contra fugas de identidad.

Estas pruebas no verifican que el codigo funcione: verifican que el
proyecto siga cumpliendo su promesa central. Si alguien agrega una
columna de IP "solo para depurar", o mete el relato en un payload
publico, aqui se cae.
"""

import re
from pathlib import Path

from app.db.base import Base
from app.models.denuncia import Denuncia
from app.services.eventos import (
    CLAVES_PROHIBIDAS,
    PAYLOAD_MINIMO,
    TipoEvento,
)

RAIZ = Path(__file__).resolve().parents[1]

# Fragmentos que no deben aparecer en el nombre de ninguna columna.
# Se buscan como subcadena, asi que "ip" cubre "ip_origen" y "client_ip".
TERMINOS_PROHIBIDOS = (
    "ip_",
    "_ip",
    "correo",
    "email",
    "telefono",
    "phone",
    "user_agent",
    "navegador",
    "huella",
    "fingerprint",
    "cookie",
    "sesion",
    "session",
    "denunciante_id",
    "identidad_real",
    "nombre_real",
    "cedula",
    "dni",
)


def test_no_existe_tabla_de_denunciantes():
    """La ausencia es intencional: si no hay donde guardar la identidad,
    no hay como revelarla despues."""
    tablas = set(Base.metadata.tables)
    for prohibida in ("denunciantes", "usuarios", "sesiones", "accesos"):
        assert prohibida not in tablas, prohibida


def test_ninguna_columna_delata_al_denunciante():
    """Recorre TODO el esquema, no solo la tabla denuncias."""
    hallazgos = []
    for nombre_tabla, tabla in Base.metadata.tables.items():
        for columna in tabla.columns:
            nombre = columna.name.lower()
            for termino in TERMINOS_PROHIBIDOS:
                if termino in nombre:
                    hallazgos.append(f"{nombre_tabla}.{columna.name}")
    assert not hallazgos, f"Columnas sospechosas: {hallazgos}"


def test_denuncias_solo_tiene_las_columnas_previstas():
    """Lista cerrada: cualquier columna nueva obliga a revisar esta prueba
    de forma deliberada, en vez de colarse sin que nadie lo note."""
    esperadas = {
        "id",
        "codigo_hash",
        "categoria_id",
        "institucion_id",
        "nivel_identidad",
        "gravedad",
        "estado",
        "relato",
        "creado_en",
    }
    reales = {c.name for c in Denuncia.__table__.columns}
    assert reales == esperadas, f"Diferencia: {reales ^ esperadas}"


def test_el_codigo_se_guarda_hasheado_y_es_unico():
    columna = Denuncia.__table__.columns["codigo_hash"]
    assert columna.unique, "Sin unique, dos casos podrian colisionar"
    assert not columna.nullable


def test_ningun_payload_admite_claves_prohibidas():
    """Cada evento declara sus claves minimas; ninguna puede identificar."""
    for tipo in TipoEvento:
        claves = set(PAYLOAD_MINIMO[tipo])
        filtradas = claves & CLAVES_PROHIBIDAS
        assert not filtradas, f"{tipo.value}: {filtradas}"


def test_ningun_payload_lleva_contenido_libre():
    """La bitacora prueba que algo ocurrio, no que se dijo. El relato y el
    cuerpo de los mensajes se quedan fuera del registro publico."""
    for tipo in TipoEvento:
        for clave in PAYLOAD_MINIMO[tipo]:
            assert clave not in ("relato", "cuerpo", "texto", "contenido"), (
                f"{tipo.value} expondria contenido en un registro publico"
            )


def test_uvicorn_corre_sin_access_log():
    """Por defecto uvicorn escribe la IP del cliente en cada peticion. Si
    alguien quita esta bandera, el anonimato se rompe en el log antes de
    llegar a la base."""
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    assert "--no-access-log" in dockerfile


def test_la_configuracion_no_habilita_registro_de_ip():
    from app.core.config import Settings

    assert Settings().registrar_ip is False


def test_el_codigo_fuente_no_registra_la_peticion():
    """Busca llamadas de log que reciban el objeto Request: seria la via
    mas facil de filtrar una IP sin darse cuenta."""
    sospechosas = []
    patron = re.compile(r"log\w*\.\w+\(.*request", re.IGNORECASE)
    for archivo in (RAIZ / "app").rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        if patron.search(texto):
            sospechosas.append(archivo.name)
    assert not sospechosas, f"Posible registro de peticion: {sospechosas}"