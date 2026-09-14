"""bateria de denuncias sinteticas

Datos de demostracion. NO se aplica por defecto: solo cuando la variable
de entorno PNDC_SEMILLA_DEMO vale "1". Asi el portal arranca vacio en un
entorno limpio, que es lo correcto, y la bateria se carga a proposito.

    PowerShell:  $env:PNDC_SEMILLA_DEMO = "1"; alembic upgrade head

LA CADENA DE EVENTOS TAMBIEN SE SIEMBRA
Sembrar denuncias sin sus eventos dejaria la bitacora contando una
historia distinta a la del portal. Por eso se calculan aqui los hashes
encadenados, con la misma formula que la aplicacion.

El calculo se reimplementa en vez de importarse de app.services.cadena:
una migracion es un registro historico y debe seguir funcionando aunque
ese servicio cambie.

Revision ID: 0014
Revises: 0013
"""
import hashlib
import json
import os
import random
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from alembic import op
from sqlalchemy import Boolean, Integer, String, Text, column, table
from sqlalchemy import Enum as SAEnum

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIVADA = os.getenv("PNDC_SEMILLA_DEMO") == "1"

SEPARADOR = "|"

# Semilla fija: la bateria es identica en cada entorno, asi la demo es
# reproducible y el ranking sale igual en todas las maquinas.
ALEATORIO = random.Random(20260914)


def hash_evento(tipo: str, payload: dict, anterior: str | None) -> str:
    canonico = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    material = SEPARADOR.join([tipo, canonico, anterior or ""])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


# (categoria, institucion, estado, gravedad, texto_publicado)
CASOS = [
    # --- Publicados: dan forma al ranking ---
    ("Soborno", "Municipalidad de San Andres del Valle", "publicada", "media",
     "Se recibio una denuncia por presunto cobro de pagos irregulares para agilizar permisos de construccion. El caso fue revisado y se considera que amerita seguimiento."),
    ("Soborno", "Municipalidad de San Andres del Valle", "publicada", "media",
     "Una segunda denuncia senala la misma practica de cobros no oficiales en la ventanilla de tramites municipales."),
    ("Licitacion amanada", "Secretaria de Obras Regionales", "publicada", "alta",
     "Se denuncio que un contrato de obra vial se adjudico a una empresa que presento la unica oferta valida tras descalificaciones cuestionables de los demas participantes."),
    ("Licitacion amanada", "Secretaria de Obras Regionales", "publicada", "media",
     "Se reporta que las bases de una licitacion incluian requisitos tecnicos que solo un proveedor podia cumplir."),
    ("Nepotismo", "Instituto de Pensiones del Magisterio", "publicada", "baja",
     "Se denuncio la contratacion de personal con vinculo familiar directo con autoridades del instituto, sin concurso previo."),
    ("Desvio de fondos publicos", "Empresa Nacional de Energia Costera", "publicada", "alta",
     "Se denuncio que fondos asignados a mantenimiento de red se habrian destinado a gastos no relacionados con el objeto presupuestado."),
    ("Uso indebido de recursos del Estado", "Municipalidad de Puerto Lindo", "publicada", "baja",
     "Se reporta el uso de vehiculos municipales para actividades ajenas a la funcion publica."),
    ("Trafico de influencias", "Comision Reguladora de Agua Potable", "publicada", "media",
     "Se denuncio que un funcionario habria intervenido para acelerar la resolucion de un tramite a favor de un tercero."),

    # --- En proceso: dan cuerpo a la cola de triaje ---
    ("Conflicto de intereses", "Portuaria del Litoral", "en_triaje", None, None),
    ("Abuso de autoridad", "Juzgado Segundo de lo Contencioso", "en_triaje", None, None),
    ("Soborno", "Juzgado Segundo de lo Contencioso", "en_triaje", None, None),
    ("Enriquecimiento ilicito", "Secretaria de Salud Territorial", "en_triaje", None, None),
    ("Otro", "Instituto de Vivienda Popular", "en_triaje", None, None),

    ("Desvio de fondos publicos", "Secretaria de Educacion del Valle", "en_revision_doble", "alta", None),
    ("Licitacion amanada", "Constructora Vallecrest", "en_revision_doble", "alta", None),
    ("Enriquecimiento ilicito", "Tribunal de Cuentas Regional", "en_revision_doble", "alta", None),

    # --- Criticos derivados: no se publican nunca ---
    ("Desvio de fondos publicos", "Suministros Medicos del Norte", "derivada", "critica", None),
    ("Abuso de autoridad", "Municipalidad de Villa Esperanza", "derivada", "critica", None),

    # --- Rechazados ---
    ("Otro", "Corte Regional de Apelaciones", "rechazada", "baja", None),
    ("Nepotismo", "Comision Reguladora de Telecomunicaciones", "rechazada", "baja", None),
]

RELATO_BASE = (
    "Los hechos ocurrieron durante el ultimo trimestre. Se observaron "
    "irregularidades en el manejo de los procedimientos administrativos "
    "correspondientes, con documentacion que no coincide con lo ejecutado. "
    "Se solicita revision de los registros del periodo senalado."
)


def upgrade() -> None:


    if not ACTIVADA:
        print(
            "Semilla de demostracion omitida. "
            "Para cargarla: PNDC_SEMILLA_DEMO=1 alembic upgrade head"
        )
        return

    conexion = op.get_bind()

 

    # Mapas nombre -> id
    from sqlalchemy import text as sql
    
    categorias = {
        nombre: ident
        for ident, nombre in conexion.execute(
            sql("SELECT id, nombre FROM categorias")
        )
    }
    instituciones = {
        nombre: ident
        for ident, nombre in conexion.execute(
            sql("SELECT id, nombre FROM instituciones")
        )
    }
    revisores = [
        ident for (ident,) in conexion.execute(sql("SELECT id FROM revisores ORDER BY id"))
    ]

    if not revisores:
        raise RuntimeError("No hay revisores sembrados: falta la migracion 0012")

    # Hash del ultimo evento existente, para encadenar sin romper nada.
    ultimo = conexion.execute(
        sql("SELECT hash_actual FROM bitacora ORDER BY indice DESC LIMIT 1")
    ).scalar_one_or_none()

    eventos: list[dict] = []
    anterior = ultimo
    faltantes = {
        nombre
        for _, nombre, *_ in CASOS
        if nombre not in instituciones
    } | {
        nombre
        for nombre, *_ in CASOS
        if nombre not in categorias
    }
    if faltantes:
        raise RuntimeError(
            f"La bateria referencia nombres que no existen en el catalogo: "
            f"{sorted(faltantes)}"
        )
    def emitir(tipo: str, payload: dict, cuando: datetime) -> None:
        nonlocal anterior
        actual = hash_evento(tipo, payload, anterior)
        eventos.append(
            {
                "tipo_evento": tipo,
                "payload": json.dumps(payload, ensure_ascii=False),
                "hash_anterior": anterior,
                "hash_actual": actual,
                "creado_en": cuando,
            }
        )
        anterior = actual

    inicio = datetime.now(timezone.utc) - timedelta(days=75)
    fila_denuncia = 0

    for indice, (cat, inst, estado, gravedad, texto) in enumerate(CASOS):
        cat_id = categorias[cat]
        inst_id = instituciones[inst]
        creado = inicio + timedelta(days=indice * 3, hours=ALEATORIO.randint(0, 20))

        # Hash falso pero con la forma correcta: estas denuncias son
        # sinteticas y su codigo no existe, asi que nadie puede consultarlas.
        codigo_hash = f"$argon2id$demo${hashlib.sha256(str(indice).encode()).hexdigest()}"

        resultado = conexion.execute(
            sql(
                "INSERT INTO denuncias "
                "(codigo_hash, categoria_id, institucion_id, nivel_identidad, "
                " gravedad, estado, relato, creado_en) "
                "VALUES (:h, :c, :i, 'anonimo', "
                " CAST(:g AS gravedad), CAST(:e AS estado_denuncia), :r, :t) "
                "RETURNING id"
            ),
            {
                "h": codigo_hash,
                "c": cat_id,
                "i": inst_id,
                "g": gravedad,
                "e": estado,
                "r": RELATO_BASE,
                "t": creado,
            },
        )
        denuncia_id = resultado.scalar_one()
        fila_denuncia += 1

        emitir(
            "denuncia_recibida",
            {
                "denuncia_id": denuncia_id,
                "categoria_id": cat_id,
                "institucion_id": inst_id,
                "nivel_identidad": "anonimo",
            },
            creado,
        )

        if estado == "recibida":
            continue

        revisor = ALEATORIO.choice(revisores)
        momento = creado + timedelta(days=2)

        emitir(
            "revisor_asignado",
            {"denuncia_id": denuncia_id, "revisor_id": revisor},
            momento,
        )
        conexion.execute(
            sql(
                "INSERT INTO asignaciones_revision "
                "(denuncia_id, revisor_id, completada, creado_en) "
                "VALUES (:d, :r, true, :t)"
            ),
            {"d": denuncia_id, "r": revisor, "t": momento},
        )

        if gravedad:
            emitir(
                "gravedad_asignada",
                {
                    "denuncia_id": denuncia_id,
                    "revisor_id": revisor,
                    "gravedad": gravedad,
                },
                momento + timedelta(hours=1),
            )

        if estado in ("publicada", "rechazada", "derivada"):
            decision = {
                "publicada": "procede",
                "rechazada": "rechaza",
                "derivada": "deriva",
            }[estado]

            conexion.execute(
                sql(
                    "INSERT INTO revisiones "
                    "(denuncia_id, revisor_id, decision, notas, creado_en) "
                    "VALUES (:d, :r, CAST(:dec AS decision_revision), :n, :t)"
                ),
                {
                    "d": denuncia_id,
                    "r": revisor,
                    "dec": decision,
                    "n": "Caso sintetico de demostracion.",
                    "t": momento + timedelta(days=1),
                },
            )
            emitir(
                "revision_emitida",
                {
                    "denuncia_id": denuncia_id,
                    "revisor_id": revisor,
                    "decision": decision,
                },
                momento + timedelta(days=1),
            )

        if estado == "publicada" and texto:
            publicado = momento + timedelta(days=3)
            pub_id = conexion.execute(
                sql(
                    "INSERT INTO publicaciones "
                    "(denuncia_id, texto_redactado, creado_en) "
                    "VALUES (:d, :t, :c) RETURNING id"
                ),
                {"d": denuncia_id, "t": texto, "c": publicado},
            ).scalar_one()

            emitir(
                "caso_publicado",
                {
                    "denuncia_id": denuncia_id,
                    "revisor_id": revisores[-1],  # el supervisor
                    "publicacion_id": pub_id,
                },
                publicado,
            )

        if estado == "derivada":
            derivado = momento + timedelta(days=2)
            der_id = conexion.execute(
                sql(
                    "INSERT INTO derivaciones "
                    "(denuncia_id, autoridad, motivo, creado_en) "
                    "VALUES (:d, :a, :m, :c) RETURNING id"
                ),
                {
                    "d": denuncia_id,
                    "a": "Fiscalia Especial Anticorrupcion",
                    "m": "Caso clasificado como critico.",
                    "c": derivado,
                },
            ).scalar_one()

            emitir(
                "caso_derivado",
                {
                    "denuncia_id": denuncia_id,
                    "revisor_id": revisor,
                    "derivacion_id": der_id,
                    "autoridad": "Fiscalia Especial Anticorrupcion",
                },
                derivado,
            )

        if estado == "rechazada":
            emitir(
                "caso_rechazado",
                {"denuncia_id": denuncia_id, "revisor_id": revisor},
                momento + timedelta(days=1, hours=2),
            )

    bitacora = table(
        "bitacora",
        column("tipo_evento", String),
        column("payload", Text),
        column("hash_anterior", String),
        column("hash_actual", String),
    )

    for evento in eventos:
        conexion.execute(
            sql(
                "INSERT INTO bitacora "
                "(tipo_evento, payload, hash_anterior, hash_actual, creado_en) "
                "VALUES (:t, CAST(:p AS jsonb), :ha, :hc, :c)"
            ),
            {
                "t": evento["tipo_evento"],
                "p": evento["payload"],
                "ha": evento["hash_anterior"],
                "hc": evento["hash_actual"],
                "c": evento["creado_en"],
            },
        )

    print(f"Semilla de demostracion: {fila_denuncia} denuncias, {len(eventos)} eventos")


def downgrade() -> None:
    # La bitacora NO se puede borrar: las reglas del motor lo impiden, y
    # ese es justamente el punto del proyecto. Los eventos sinteticos se
    # quedan. Para partir de cero: docker compose down -v
    op.execute("DELETE FROM publicaciones")
    op.execute("DELETE FROM derivaciones")
    op.execute("DELETE FROM revisiones")
    op.execute("DELETE FROM asignaciones_revision")
    op.execute("DELETE FROM denuncias")