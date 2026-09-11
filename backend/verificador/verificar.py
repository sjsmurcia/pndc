"""Verificador independiente de la cadena de bitacora.

POR QUE ES UN PROGRAMA APARTE
Si la verificacion viviera dentro de la misma API que escribe la bitacora,
verificarse a si misma no probaria nada: quien manipulara la base podria
manipular tambien el verificador. Este programa se ejecuta por separado,
con su propio rol de solo lectura, y recalcula la cadena desde cero sin
confiar en nada de lo que la aplicacion afirme.

USO
    python verificar.py
    python verificar.py --url postgresql://usuario:clave@host:puerto/base
    python verificar.py --json
"""

import argparse
import hashlib
import json
import os
import sys

import psycopg

SEPARADOR = "|"

# Valores por defecto: rol de solo lectura contra el contenedor.
URL_POR_DEFECTO = os.getenv(
    "VERIFICADOR_DATABASE_URL",
    "postgresql://pndc_verificador:pndc_verif_dev@localhost:5433/pndc",
)


def payload_canonico(payload: dict) -> str:
    """Debe coincidir EXACTAMENTE con la serializacion de la aplicacion.

    Si difiere en un espacio, todos los hashes salen distintos y la cadena
    parecera rota aunque este intacta. Por eso se reimplementa aqui en vez
    de importarla: el verificador no depende del codigo que verifica.
    """
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


def verificar(url: str) -> dict:
    """Recalcula la cadena completa y reporta el resultado."""
    with psycopg.connect(url) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT indice, tipo_evento, payload, hash_anterior, "
                "hash_actual, creado_en FROM bitacora ORDER BY indice ASC"
            )
            eventos = cursor.fetchall()

    if not eventos:
        return {
            "intacta": True,
            "eventos": 0,
            "mensaje": "La bitacora esta vacia.",
        }

    esperado: str | None = None

    for indice, tipo, payload, hash_anterior, hash_actual, creado in eventos:
        # 1. El eslabon debe apuntar al hash real del evento anterior.
        #    Si alguien borro un evento intermedio, esto falla.
        if hash_anterior != esperado:
            return {
                "intacta": False,
                "eventos": len(eventos),
                "indice_roto": indice,
                "motivo": "eslabon_roto",
                "mensaje": (
                    f"El evento {indice} apunta a un hash que no corresponde "
                    "al evento anterior. Falta un evento o se altero su "
                    "contenido."
                ),
                "esperaba": esperado,
                "encontro": hash_anterior,
                "creado_en": str(creado),
            }

        # 2. El hash guardado debe coincidir con el recalculado.
        #    Si alguien altero el payload, esto falla.
        recalculado = calcular_hash(tipo, payload, hash_anterior)
        if recalculado != hash_actual:
            return {
                "intacta": False,
                "eventos": len(eventos),
                "indice_roto": indice,
                "motivo": "contenido_alterado",
                "mensaje": (
                    f"El contenido del evento {indice} no corresponde a su "
                    "hash. El registro fue modificado despues de escribirse."
                ),
                "esperaba": recalculado,
                "encontro": hash_actual,
                "tipo_evento": tipo,
                "creado_en": str(creado),
            }

        esperado = hash_actual

    return {
        "intacta": True,
        "eventos": len(eventos),
        "primer_hash": eventos[0][4],
        "ultimo_hash": eventos[-1][4],
        "mensaje": f"Cadena intacta: {len(eventos)} eventos verificados.",
    }


def imprimir_humano(resultado: dict) -> None:
    ancho = 64
    print("=" * ancho)
    print("VERIFICADOR DE INTEGRIDAD — PNDC")
    print("=" * ancho)

    if resultado["intacta"]:
        print(f"\n  ESTADO: CADENA INTACTA")
        print(f"  Eventos verificados: {resultado['eventos']}")
        if resultado["eventos"]:
            print(f"  Primer hash: {resultado['primer_hash'][:32]}...")
            print(f"  Ultimo hash: {resultado['ultimo_hash'][:32]}...")
        print("\n  Ningun evento fue alterado ni eliminado.")
    else:
        print(f"\n  ESTADO: CADENA ROTA")
        print(f"  Eventos leidos: {resultado['eventos']}")
        print(f"  Ruptura en el evento: {resultado['indice_roto']}")
        print(f"  Motivo: {resultado['motivo']}")
        print(f"\n  {resultado['mensaje']}")
        print(f"\n  Hash esperado:   {resultado['esperaba']}")
        print(f"  Hash encontrado: {resultado['encontro']}")

    print("\n" + "=" * ancho)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica la integridad de la bitacora del PNDC."
    )
    parser.add_argument(
        "--url",
        default=URL_POR_DEFECTO,
        help="Cadena de conexion. Debe usar un rol de solo lectura.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en JSON para integrarla en otras herramientas.",
    )
    args = parser.parse_args()

    try:
        resultado = verificar(args.url)
    except psycopg.Error as exc:
        print(f"No se pudo conectar a la base de datos: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        imprimir_humano(resultado)

    # Codigo de salida distinto de cero si la cadena esta rota: permite
    # usarlo en un cron o en una tuberia de CI.
    return 0 if resultado["intacta"] else 1


if __name__ == "__main__":
    sys.exit(main())