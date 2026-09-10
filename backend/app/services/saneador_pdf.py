"""saneamiento de pdf por rasterizacion .
"""

import hashlib
from dataclasses import dataclass

import pymupdf

#150 ppp
RESOLUCION=150 
#para no agotar la memoria
LIMITE_PAGINAS = 60 

@dataclass(frozen=True)
class PdfSaneado:
    contenido:bytes
    sha256: str
    paginas:int
    tenia_texto:bool
class SaneamientoPdfFallido(Exception):
    """El documento no se pudo procesar."""

def sanear_pdf(contenido:bytes)-> PdfSaneado:
    """rasterizar cada pagina y reconstruye el documento"""
    try:
        origen=pymupdf.open(stream=contenido, filetype="pdf")
    except Exception as exc:
        raise SaneamientoPdfFallido(
        "El archivo no es un PDF valido o esta danado"
        ) from exc 
    with origen:
        if origen.needs_pass:
            raise SaneamientoPdfFallido(
                "El documento esta protegido con contrasena"
            )

        if origen.page_count == 0:
            raise SaneamientoPdfFallido("El documento no tiene paginas")
            

        if origen.page_count > LIMITE_PAGINAS:
            raise SaneamientoPdfFallido(
                f"El documento supera las {LIMITE_PAGINAS} paginas"
            )

        tenia_texto = any(pagina.get_text().strip() for pagina in origen)
        total_paginas = origen.page_count
        destino = pymupdf.open()
        matriz=pymupdf.Matrix(RESOLUCION / 72, RESOLUCION /72)

        try:
            for pagina in origen:
                imagen= pagina.get_pixmap(matrix=matriz, alpha=False)

                nueva=destino.new_page(
                    width=pagina.rect.width, height=pagina.rect.height
                )
                nueva.insert_image(nueva.rect, pixmap=imagen)
            destino.set_metadata({})

            salida=destino.tobytes(garbage=4, deflate=True)
        finally:
            destino.close()

    return PdfSaneado(
        contenido=salida,
        sha256=hashlib.sha256(salida).hexdigest(),
        paginas=total_paginas,
        tenia_texto=tenia_texto,
    )

def tiene_texto_seleccionable(contenido:bytes)-> bool:
    """Comprueba si un PDF conserva texto extraible."""

    try: 
        with pymupdf.open(stream=contenido, filetype="pdf") as doc:
            return "\n".join(pagina.get_text() for pagina in doc)
    except Exception:
        return ""

def extraer_texto(contenido: bytes) -> str:
    """Devuelve todo el texto extraible. Solo para pruebas y demo."""
    try:
        with pymupdf.open(stream=contenido, filetype="pdf") as doc:
            return "\n".join(pagina.get_text() for pagina in doc)
    except Exception:
        return ""