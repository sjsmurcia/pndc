from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.v1.seguimiento import buscar_por_codigo
from app.core.config import get_settings
from app.models.evidencia import Evidencia
from app.services.deteccion import ArchivoRechazado, detectar
from app.services.saneador_imagen import SaneamientoFallido, sanear
from app.db.session import get_db
from app.models.catalogo import Categoria, Institucion
from app.models.denuncia import Denuncia
from app.models.enums import EstadoDenuncia
from app.schemas.denuncia import DenunciaCreada, DenunciaCrear, EvidenciaSubida
from app.services import cadena
from app.services.codigo import generar_codigo, hashear_codigo
from app.services.eventos import TipoEvento
from app.models.enums import EstadoDenuncia, NivelIdentidad
from app.services.codigo import generar_codigo, generar_seudonimo, hashear_codigo
from dataclasses import dataclass

from app.services.saneador_pdf import SaneamientoPdfFallido, sanear_pdf
from app.services.antispam import (
    EnvioRechazado,
    emitir_reto,
    honeypot_relleno,
    registrar_envio,
    verificar_prueba,
)

router = APIRouter(prefix="/denuncias", tags=["denuncias"])


DIR_EVIDENCIAS = Path(get_settings().pndc_quarantine_dir) / "evidencias"


@dataclass(frozen=True)
class ArchivoLimpio:
    """Resultado del saneamiento, sea imagen o PDF.

    ancho y alto quedan en cero para PDF: la nocion de dimensiones no
    aplica a un documento de varias paginas.
    """

    contenido: bytes
    mime: str
    sha256: str
    ancho: int
    alto: int


def guardar_evidencia(evidencia_id: int, limpia) -> str:
    """Escribe la version saneada y devuelve su ruta relativa.

    El nombre lo genera el sistema: el nombre original puede llevar el
    nombre real de quien envia, la ruta de su disco, o el numero de caso
    de otro tramite.
    """
    DIR_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }[limpia.mime]
    nombre = f"{evidencia_id:08d}{extension}"
    (DIR_EVIDENCIAS / nombre).write_bytes(limpia.contenido)
    return f"evidencias/{nombre}"


def borrar_evidencia(ruta_relativa: str) -> None:
    """Elimina un archivo saneado que quedo sin su fila en la base.

    missing_ok=True: si el archivo ya no esta, no hay nada que hacer.
    """
    nombre = Path(ruta_relativa).name
    (DIR_EVIDENCIAS / nombre).unlink(missing_ok=True)


@router.post(
    "",
    response_model=DenunciaCreada,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una denuncia anonima",
)
def crear_denuncia(
    datos: DenunciaCrear, db: Session = Depends(get_db)
) -> DenunciaCreada:
    # capa 1: campo
    if honeypot_relleno(datos.sitio_web):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envio no valido")
    # capa 2: prueba de trabajo
    if not datos.reto or not datos.nonce:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Falta la prueba de trabajo. Recargue la pagina.")
    # capa 3: limite del formulario
    try:
        verificar_prueba(datos.reto, datos.nonce)
        registrar_envio()
    except EnvioRechazado as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc
    # registra una denuncia y emite el codigo del seguimiento.

    if not db.get(Categoria, datos.categoria_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria Inexistente")
    if not db.get(Institucion, datos.institucion_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institucion inexistente")
    codigo = generar_codigo()
    # solo para el nivel de seudonimo
    seudonimo = (
        generar_seudonimo()
        if datos.nivel_identidad == NivelIdentidad.SEUDONIMO
        else None
    )
    denuncia = Denuncia(
        codigo_hash=hashear_codigo(codigo),
        categoria_id=datos.categoria_id,
        institucion_id=datos.institucion_id,
        nivel_identidad=datos.nivel_identidad,
        estado=EstadoDenuncia.RECIBIDA,
        relato=datos.relato,
        seudonimo=seudonimo,
    )
    db.add(denuncia)
    db.flush()  # asignar el id sin cerrar la transaccion

    # el evento entra en la misma transaccion. si el alta falla la bitacora falla

    cadena.registrar(
        db,
        TipoEvento.DENUNCIA_RECIBIDA,
        {
            "denuncia_id": denuncia.id,
            "categoria_id": denuncia.categoria_id,
            "institucion_id": denuncia.institucion_id,
            "nivel_identidad": denuncia.nivel_identidad.value,
        },
    )

    return DenunciaCreada(
        denuncia_id=denuncia.id,
        codigo=codigo,
        estado=denuncia.estado,
        creado_en=denuncia.creado_en,
    )


@router.post(
    "/{denuncia_id}/evidencias",
    response_model=EvidenciaSubida,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar evidencia a una denuncia",
)
def subir_evidencia(
    denuncia_id: int,
    codigo: Annotated[str, Form()],
    archivo: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
) -> EvidenciaSubida:

    denuncia = buscar_por_codigo(db, codigo)
    if denuncia is None or denuncia.id != denuncia_id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Codigo no valido o caso inexistente"
        )

    contenido = archivo.file.read()
    # El tipo se decide por los bytes, no por el nombre del archivo.
    try:
        formato = detectar(contenido)
    except ArchivoRechazado as exc:
        cadena.registrar(
            db,
            TipoEvento.EVIDENCIA_RECHAZADA,
            {
                "denuncia_id": denuncia.id,
                "motivo": str(exc),
                "mime_detectado": "desconocido",
            },
        )
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc

        # Cada formato delata de una manera distinta, asi que cada uno tiene
    # su propio saneador. Imagenes: reescritura de pixeles. PDF:
    # rasterizacion, porque un rectangulo negro no borra el texto debajo.
    try:
        if formato.mime == "application/pdf":
            pdf = sanear_pdf(contenido)
            limpia = ArchivoLimpio(
                contenido=pdf.contenido,
                mime="application/pdf",
                sha256=pdf.sha256,
                ancho=0,
                alto=0,
            )
        else:
            imagen = sanear(contenido, formato)
            limpia = ArchivoLimpio(
                contenido=imagen.contenido,
                mime=imagen.mime,
                sha256=imagen.sha256,
                ancho=imagen.ancho,
                alto=imagen.alto,
            )
    except (SaneamientoFallido, SaneamientoPdfFallido) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    # A partir de aqui el original ya no se usa. No se guarda en ningun lado.
    del contenido

    evidencia = Evidencia(
        denuncia_id=denuncia.id,
        url="",  # se completa tras conocer el id
        sha256=limpia.sha256,
        mime=limpia.mime,
        sanitizada=True,
    )
    db.add(evidencia)
    db.flush()

    # El sistema de archivos NO participa de la transaccion: si algo falla
    # despues de escribir, el rollback deshace la fila pero el archivo se
    # queda huerfano. Por eso se limpia a mano.
    ruta = guardar_evidencia(evidencia.id, limpia)

    try:
        evidencia.url = ruta

        cadena.registrar(
            db,
            TipoEvento.EVIDENCIA_RECIBIDA,
            {
                "denuncia_id": denuncia.id,
                "evidencia_id": evidencia.id,
                "mime": limpia.mime,
            },
        )
        cadena.registrar(
            db,
            TipoEvento.EVIDENCIA_SANEADA,
            {
                "evidencia_id": evidencia.id,
                "sha256": limpia.sha256,
                "mime_final": limpia.mime,
            },
        )

        return EvidenciaSubida(
            evidencia_id=evidencia.id,
            mime=limpia.mime,
            sha256=limpia.sha256,
            ancho=limpia.ancho,
            alto=limpia.alto,
            sanitizada=True,
        )
    except Exception:
        borrar_evidencia(ruta)
        raise


@router.get(
    "/reto",
    summary="Obtener un reto de prueba de trabajo",
)
def obtener_reto() -> dict:
    """El navegador debe resolver este reto antes de poder enviar.

    publico y sin autenticacion: quien va a denunciar aun no tiene codigo,
    el reto va firmado, asi que el servidor no necesita guardarlo."""
    return emitir_reto()
