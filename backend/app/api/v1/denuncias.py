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

router = APIRouter(prefix="/denuncias", tags=["denuncias"])


DIR_EVIDENCIAS = Path(get_settings().pndc_quarantine_dir) / "evidencias"


def guardar_evidencia(evidencia_id: int, limpia) -> str:
    """Escribe la version saneada y devuelve su ruta relativa.

    El nombre lo genera el sistema: el nombre original puede llevar el
    nombre real de quien envia, la ruta de su disco, o el numero de caso
    de otro tramite.
    """
    DIR_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    extension = ".jpg" if limpia.mime == "image/jpeg" else ".png"
    nombre = f"{evidencia_id:08d}{extension}"
    (DIR_EVIDENCIAS / nombre).write_bytes(limpia.contenido)
    return f"evidencias/{nombre}"


@router.post(
    "",
    response_model=DenunciaCreada,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una denuncia anonima",
)
def crear_denuncia(
    datos: DenunciaCrear, db: Session = Depends(get_db)
) -> DenunciaCreada:
    # registra una denuncia y emite el codigo del seguimiento.

    if not db.get(Categoria, datos.categoria_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria Inexistente")
    if not db.get(Institucion, datos.institucion_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institucion inexistente")
    codigo = generar_codigo()

    denuncia = Denuncia(
        codigo_hash=hashear_codigo(codigo),
        categoria_id=datos.categoria_id,
        institucion_id=datos.institucion_id,
        nivel_identidad=datos.nivel_identidad,
        estado=EstadoDenuncia.RECIBIDA,
        relato=datos.relato,
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

    try:
        limpia = sanear(contenido, formato)
    except SaneamientoFallido as exc:
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

    ruta = guardar_evidencia(evidencia.id, limpia)
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
