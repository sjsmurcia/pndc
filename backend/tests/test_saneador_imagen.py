import io

import piexif
import pytest
from PIL import Image

from app.services.deteccion import detectar
from app.services.saneador_imagen import (
    SaneamientoFallido,
    sanear,
    tiene_metadatos,
)


def imagen_con_exif() -> bytes:
    """Fabrica un JPEG con GPS, marca, modelo y numero de serie.

    Es lo que lleva una foto tomada con un telefono: coordenadas exactas
    del lugar y huella del equipo.
    """
    img = Image.new("RGB", (120, 80), color=(30, 90, 160))

    exif = {
        "0th": {
            piexif.ImageIFD.Make: b"ACME",
            piexif.ImageIFD.Model: b"Telefono X200",
            piexif.ImageIFD.Software: b"CamaraApp 3.1",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2026:03:14 09:12:44",
            piexif.ExifIFD.BodySerialNumber: b"SN-88213774",
        },
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: ((14, 1), (5, 1), (0, 1)),
            piexif.GPSIFD.GPSLongitudeRef: b"W",
            piexif.GPSIFD.GPSLongitude: ((87, 1), (12, 1), (0, 1)),
        },
        "1st": {},
        "thumbnail": None,
    }

    salida = io.BytesIO()
    img.save(salida, format="JPEG", exif=piexif.dump(exif))
    return salida.getvalue()


def imagen_png() -> bytes:
    salida = io.BytesIO()
    Image.new("RGBA", (60, 40), color=(200, 30, 30, 255)).save(
        salida, format="PNG"
    )
    return salida.getvalue()


def test_la_imagen_de_prueba_si_tiene_metadatos():
    """Control: si esto falla, las demas pruebas no demuestran nada."""
    assert tiene_metadatos(imagen_con_exif())


def test_el_saneado_no_conserva_metadatos():
    """La prueba central del proyecto: la foto entra con GPS y sale sin el."""
    original = imagen_con_exif()
    resultado = sanear(original, detectar(original))
    assert not tiene_metadatos(resultado.contenido)


def test_no_queda_rastro_del_equipo_en_los_bytes():
    """Busca las cadenas del fabricante directamente en el archivo, sin
    pasar por Pillow: asi se comprueba que no quedaron escondidas."""
    original = imagen_con_exif()
    resultado = sanear(original, detectar(original))
    for rastro in (b"ACME", b"Telefono X200", b"SN-88213774", b"CamaraApp"):
        assert rastro not in resultado.contenido, rastro


def test_los_pixeles_sobreviven():
    """Sanear no debe destruir la evidencia: mismas dimensiones y color."""
    original = imagen_con_exif()
    resultado = sanear(original, detectar(original))
    assert (resultado.ancho, resultado.alto) == (120, 80)
    with Image.open(io.BytesIO(resultado.contenido)) as img:
        assert img.getpixel((60, 40))[2] > 100  # sigue siendo azulado


def test_el_archivo_saneado_es_distinto_del_original():
    original = imagen_con_exif()
    resultado = sanear(original, detectar(original))
    assert resultado.contenido != original


def test_devuelve_sha256_del_archivo_saneado():
    import hashlib

    original = imagen_con_exif()
    resultado = sanear(original, detectar(original))
    assert resultado.sha256 == hashlib.sha256(resultado.contenido).hexdigest()
    assert len(resultado.sha256) == 64


def test_png_se_sanea():
    original = imagen_png()
    resultado = sanear(original, detectar(original))
    assert resultado.mime == "image/png"
    assert not tiene_metadatos(resultado.contenido)


def test_sanear_es_idempotente():
    """Sanear dos veces no degrada mas alla de la recompresion inicial."""
    original = imagen_con_exif()
    una = sanear(original, detectar(original))
    dos = sanear(una.contenido, detectar(una.contenido))
    assert (dos.ancho, dos.alto) == (una.ancho, una.alto)


def test_imagen_truncada_falla_limpio():
    """Un archivo cortado debe dar SaneamientoFallido, no reventar."""
    original = imagen_con_exif()
    formato = detectar(original)
    with pytest.raises(SaneamientoFallido):
        sanear(original[: len(original) // 3], formato)