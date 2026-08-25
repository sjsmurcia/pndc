"""Saneamiento de imagenes.

NO se borran los campos EXIF uno por uno: siempre queda algo. Perfiles de
color, campos propietarios del fabricante, y sobre todo la MINIATURA
incrustada, que en muchos casos conserva la foto tal como estaba ANTES de
recortarla o editarla. Ha habido filtraciones reales por eso.

Lo que se hace es construir una imagen NUEVA a partir de los pixeles del
original. Todo lo que no sea un pixel queda fuera por construccion, no por
una lista de campos que alguien tuvo que acordarse de incluir.
"""

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from app.services.deteccion import Formato

# Limite de pixeles contra "decompression bombs": una imagen de pocos KB
# puede declarar dimensiones enormes y agotar la memoria al descomprimirse.
Image.MAX_IMAGE_PIXELS = 50_000_000

CALIDAD_JPEG = 88


@dataclass(frozen=True)
class ImagenSaneada:
    contenido: bytes
    mime: str
    sha256: str
    ancho: int
    alto: int


class SaneamientoFallido(Exception):
    """La imagen no pudo procesarse."""


def sanear(contenido: bytes, formato: Formato) -> ImagenSaneada:
    """Devuelve una imagen nueva, sin metadatos, con los mismos pixeles."""
    try:
        with Image.open(io.BytesIO(contenido)) as original:
            # La orientacion vive en EXIF. Al descartar los metadatos se
            # perderia, y la foto saldria girada. exif_transpose aplica el
            # giro a los pixeles ANTES de tirar el EXIF.
            original = ImageOps.exif_transpose(original)

            # image.data copia solo la matriz de pixeles: ni EXIF, ni
            # miniatura incrustada, ni perfil ICC, ni campos del fabricante.
            limpia = Image.new(original.mode, original.size)
            limpia.putdata(list(original.getdata()))

            salida = io.BytesIO()
            if formato.mime == "image/jpeg":
                if limpia.mode not in ("RGB", "L"):
                    limpia = limpia.convert("RGB")
                limpia.save(
                    salida,
                    format="JPEG",
                    quality=CALIDAD_JPEG,
                    optimize=True,
                    exif=b"",  # explicito: sin bloque EXIF
                )
            else:
                limpia.save(salida, format="PNG", optimize=True)

            bytes_salida = salida.getvalue()

    except UnidentifiedImageError as exc:
        raise SaneamientoFallido("El archivo no es una imagen valida") from exc
    except Image.DecompressionBombError as exc:
        raise SaneamientoFallido(
            "La imagen declara dimensiones desproporcionadas"
        ) from exc
    except OSError as exc:
        raise SaneamientoFallido(f"Imagen corrupta o truncada: {exc}") from exc

    return ImagenSaneada(
        contenido=bytes_salida,
        mime=formato.mime,
        sha256=hashlib.sha256(bytes_salida).hexdigest(),
        ancho=limpia.width,
        alto=limpia.height,
    )


def tiene_metadatos(contenido: bytes) -> bool:
    """Comprueba si una imagen conserva EXIF o miniatura incrustada.

    Existe para las pruebas y para la demostracion: permite mostrar el
    antes y el despues del saneamiento.
    """
    try:
        with Image.open(io.BytesIO(contenido)) as img:
            if img.getexif():
                return True
            return bool(getattr(img, "info", {}).get("exif"))
    except Exception:
        return False
