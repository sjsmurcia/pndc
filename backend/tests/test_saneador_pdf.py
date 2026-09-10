import pymupdf
import pytest

from app.services.saneador_pdf import (
    LIMITE_PAGINAS,
    SaneamientoPdfFallido,
    extraer_texto,
    sanear_pdf,
    tiene_texto_seleccionable,
)

SECRETO = "Ing. Ramiro Valdes Cortes"


def pdf_con_texto_tapado() -> bytes:
    """El error clasico: dibujar un rectangulo negro sobre un nombre y
    creer que queda oculto. El texto sigue debajo, seleccionable."""
    doc = pymupdf.open()
    pagina = doc.new_page()

    pagina.insert_text((72, 100), "Acta de adjudicacion 2026-114", fontsize=13)
    pagina.insert_text((72, 140), f"Funcionario responsable: {SECRETO}", fontsize=11)
    pagina.insert_text((72, 170), "Monto adjudicado: L 4,820,000.00", fontsize=11)

    # El recuadro negro sobre el nombre. Solo cubre, no borra.
    pagina.draw_rect(
        pymupdf.Rect(215, 128, 430, 146),
        color=(0, 0, 0),
        fill=(0, 0, 0),
    )

    doc.set_metadata({"author": "Secretaria de Obras", "producer": "OficinaPro 7"})
    datos = doc.tobytes()
    doc.close()
    return datos


def pdf_de_paginas(cantidad: int) -> bytes:
    doc = pymupdf.open()
    for numero in range(cantidad):
        doc.new_page().insert_text((72, 100), f"Pagina {numero}", fontsize=12)
    datos = doc.tobytes()
    doc.close()
    return datos


def test_el_rectangulo_negro_no_oculta_nada():
    """Control. Si esto falla, las demas pruebas no demuestran nada."""
    original = pdf_con_texto_tapado()
    assert SECRETO in extraer_texto(original)


def test_tras_rasterizar_el_texto_tapado_desaparece():
    """LA PRUEBA CENTRAL de esta tarea: lo que estaba debajo del recuadro
    deja de existir, porque ya no hay texto sino pixeles."""
    original = pdf_con_texto_tapado()
    resultado = sanear_pdf(original)

    assert SECRETO not in extraer_texto(resultado.contenido)
    assert not tiene_texto_seleccionable(resultado.contenido)


def test_el_nombre_no_queda_en_los_bytes():
    """Busca la cadena en el archivo crudo, sin pasar por PyMuPDF: asi se
    comprueba que no quedo escondida en algun objeto del PDF."""
    resultado = sanear_pdf(pdf_con_texto_tapado())
    assert SECRETO.encode("utf-8") not in resultado.contenido
    assert b"Ramiro" not in resultado.contenido


def test_no_hereda_metadatos_del_original():
    resultado = sanear_pdf(pdf_con_texto_tapado())
    with pymupdf.open(stream=resultado.contenido, filetype="pdf") as doc:
        assert not doc.metadata.get("author")
        assert "OficinaPro" not in (doc.metadata.get("producer") or "")


def test_informa_que_el_original_tenia_texto():
    """El denunciante debe saber que su documento llevaba texto
    seleccionable, aunque el creyera haberlo tapado."""
    assert sanear_pdf(pdf_con_texto_tapado()).tenia_texto is True


def test_conserva_el_numero_de_paginas():
    resultado = sanear_pdf(pdf_de_paginas(4))
    assert resultado.paginas == 4
    with pymupdf.open(stream=resultado.contenido, filetype="pdf") as doc:
        assert doc.page_count == 4


def test_devuelve_sha256_del_documento_saneado():
    import hashlib

    resultado = sanear_pdf(pdf_con_texto_tapado())
    assert resultado.sha256 == hashlib.sha256(resultado.contenido).hexdigest()


def test_documento_con_demasiadas_paginas_se_rechaza():
    with pytest.raises(SaneamientoPdfFallido, match="paginas"):
        sanear_pdf(pdf_de_paginas(LIMITE_PAGINAS + 1))


def test_archivo_corrupto_falla_limpio():
    with pytest.raises(SaneamientoPdfFallido):
        sanear_pdf(b"%PDF-1.7\nesto no es un pdf de verdad")