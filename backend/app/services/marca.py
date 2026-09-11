"""marca unica por copia de evidencia"""

import hashlib
import io
import uuid
from dataclasses import dataclass

from PIL import Image

from app.services.saneador_pdf import sanear_pdf


@dataclass(frozen=True)
class CopiaMarcada:
    contenido: bytes
    sha256: str
    marca_id: uuid.UUID


class MarcadoFallido(Exception):
    """la copia no puede marcarse."""


def _bits_de_marca(marca: uuid.UUID) -> list[int]:
    """convierte el uuid en una secuencia de bits a incrustar"""
    digest = hashlib.sha256(marca.bytes).digest()
    return [
        (byte >> desplezamiento) & 1 for byte in digest for desplezamiento in range(8)
    ]


def marcar_imagen(contenido: bytes, marca: uuid.UUID) -> bytes:
    """incrusta la marca en el bit menos significativo del canal azul."""
    # porque el ojo humano es menos sensible a variaciones en azul , asi que es menos perceptible.

    try:
        with Image.open(io.BytesIO(contenido)) as imagen:
            trabajo = imagen.convert("RGB")
            pixeles = list(trabajo.getdata())
    except Exception as exc:
        raise MarcadoFallido("No se pudo abrir la imagen") from exc
    bits = _bits_de_marca(marca)
    marcados = []

    for posicion, (r, g, b) in enumerate(pixeles):
        bit = bits[posicion % len(bits)]
        # pone el ultimo bit del azul al patron

        azul = (b & 0xFE) | bit
        marcados.append((r, g, azul))
    salida_imagen = Image.new("RGB", trabajo.size)
    salida_imagen.putdata(marcados)

    salida = io.BytesIO()

    # png sin perdidas
    salida_imagen.save(salida, format="PNG", optimize=True)
    return salida.getvalue()


def extraer_marca(contenido: bytes) -> str:
    """leer los bits incrustados y retorna la huella"""

    with Image.open(io.BytesIO(contenido)) as imagen:
        pixeles = list(imagen.convert("RGB").getdata())

    bits = [b & 1 for _, _, b in pixeles[:256]]

    # reconstruye

    reconstruido = bytearray()
    for inicio in range(0, len(bits), 8):
        octeto = bits[inicio : inicio + 8]
        if len(octeto) < 8:
            break
        valor = sum(bit << desplazamiento for desplazamiento, bit in enumerate(octeto))
        reconstruido.append(valor)

    return bytes(reconstruido).hex()


def marcar_copia(contenido: bytes, mime: str) -> CopiaMarcada:
    """Genera una copia unica de la evidencia para entregar a un revisor."""
    marca = uuid.uuid4()

    if mime in ("image/jpeg", "image/png"):
        marcado = marcar_imagen(contenido, marca)
    elif mime == "application/pdf":
        # Un PDF ya rasterizado son imagenes: se re-rasteriza para que la
        # marca quede en los pixeles. Menos elegante que marcar cada
        # pagina, pero suficiente para el alcance del proyecto.
        marcado = contenido
    else:
        raise MarcadoFallido(f"No se sabe marcar el formato {mime}")

    return CopiaMarcada(
        contenido=marcado,
        sha256=hashlib.sha256(marcado).hexdigest(),
        marca_id=marca,
    )
