import pytest
from app.services.deteccion import (
    LIMITE_BYTES,
    ArchivoRechazado,
    detectar,
    extension_coincide,
)

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def test_detectar_jpeg():
    assert detectar(JPEG).mime == "image/jpeg"


def test_detecta_png():
    assert detectar(PNG).mime == "image/png"


def test_ejecutable_disfrazado_de_imagen_se_rechaza():
    ejecutable = b"MZ\x90\x00" + b"\x00" * 100
    with pytest.raises(ArchivoRechazado, match="no admitido"):
        detectar(ejecutable)


def test_pdf_todavia_no_se_acepta():
    with pytest.raises(ArchivoRechazado):
        detectar(b"%PDF-1.7\n" + b"\x00" * 100)


def test_zip_se_rechaza():
    with pytest.raises(ArchivoRechazado):
        detectar(b"PK\x03\x04" + b"\x00" * 100)


def test_svg_se_rechaza():
    with pytest.raises(ArchivoRechazado):
        detectar(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>")


def test_archivo_vacio_se_rechaza():
    with pytest.raises(ArchivoRechazado, match="vacio"):
        detectar(b"")


def test_archivo_demasiado_grande_se_rechaza():
    enorme = JPEG + b"\x00" * LIMITE_BYTES
    with pytest.raises(ArchivoRechazado, match="limite"):
        detectar(enorme)
def test_firma_incompleta_se_rechaza():
    with pytest.raises(ArchivoRechazado):
        detectar(b"\x89PNG")
def test_extension_mentirosa_no_impide_detectar():
    formato = detectar(JPEG)
    assert formato.mime == "image/jpeg"
    assert not extension_coincide("documento.pdf", formato)
def test_jpeg_acepta_ambas_extensiones():
    formato = detectar(JPEG)
    assert extension_coincide("foto.jpg", formato)
    assert extension_coincide("FOTO.JPEG", formato)