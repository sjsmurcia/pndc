"""Deteccion del tipo real de un archivo por sus bytes de cabecera.

REGLA 1 - LISTA BLANCA, NUNCA LISTA NEGRA
Una lista negra tendria que anticipar todo lo peligroso, y siempre falta
algo. Aqui solo se acepta lo que el saneador sabe procesar.

REGLA 2 - LOS BYTES, NO LA EXTENSION
La extension la elige quien sube el archivo: renombrar un ejecutable a
.jpg es trivial. Los primeros bytes los pone el formato.
"""

from dataclasses import dataclass

# Tamano maximo por archivo. Un limite explicito evita que un envio
# agote la memoria del saneador.
LIMITE_BYTES = 15 * 1024 * 1024  # 15 MB


@dataclass(frozen=True)
class Formato:
    mime: str
    extension: str
    firma: bytes
    desplazamiento: int = 0


# Firmas ("magic numbers") de los formatos aceptados en este sprint.
# PDF y Office llegan en el Sprint 3, con su propio saneador.
FORMATOS: tuple[Formato, ...] = (
    Formato("image/jpeg", ".jpg", b"\xff\xd8\xff"),
    Formato("image/png", ".png", b"\x89PNG\r\n\x1a\n"),
)


class ArchivoRechazado(Exception):
    """El archivo no pasa la lista blanca."""


def detectar(contenido: bytes) -> Formato:
    """Devuelve el formato real del archivo o lanza ArchivoRechazado.

    No recibe el nombre del archivo a proposito: si la funcion no conoce
    la extension, no puede caer en la tentacion de confiar en ella.
    """
    if not contenido:
        raise ArchivoRechazado("Archivo vacio")

    if len(contenido) > LIMITE_BYTES:
        raise ArchivoRechazado(
            f"El archivo supera el limite de {LIMITE_BYTES // (1024 * 1024)} MB"
        )

    for formato in FORMATOS:
        inicio = formato.desplazamiento
        fin = inicio + len(formato.firma)
        if contenido[inicio:fin] == formato.firma:
            return formato

    raise ArchivoRechazado(
        "Formato no admitido. Solo se aceptan imagenes JPEG y PNG."
    )


def extension_coincide(nombre_archivo: str, formato: Formato) -> bool:
    """Comprueba si la extension declarada corresponde al contenido real.

    NO se usa para decidir si el archivo se acepta: eso lo decide detectar().
    Sirve para registrar la discrepancia, que es una senal util. Un archivo
    llamado .pdf que en realidad es JPEG puede ser un error del usuario o
    un intento deliberado.
    """
    nombre = nombre_archivo.lower()
    if nombre.endswith(formato.extension):
        return True
    # JPEG admite dos extensiones validas; el Formato solo declara una.
    return formato.extension == ".jpg" and nombre.endswith(".jpeg")