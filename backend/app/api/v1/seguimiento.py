from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.denuncia import Denuncia
from app.models.evidencia import Mensaje
from app.models.enums import AutorMensaje, EstadoDenuncia
from app.schemas.denuncia import (
    DenunciaVista,
    MensajeCrear,
    MensajeVista,
    SeguimientoConsulta,
)
from app.services import cadena
from app.services.codigo import verificar_codigo
from app.services.eventos import TipoEvento

router = APIRouter(prefix="/seguimiento", tags=["seguimiento"])

ESTADOS_CERRADOS = frozenset(
    {
        EstadoDenuncia.PUBLICADA,
        EstadoDenuncia.RECHAZADA,
        EstadoDenuncia.DERIVADA,
    }
)


def buscar_por_codigo(db: Session, codigo: str) -> Denuncia | None:
    # localiza la denuncia cuyo hash coincide con el codigo
    """argon2 usa sal aleatorio, asi que el mismo codigo produce hashes
    distintos cada vez: no se puede hacer where codigo y hay que verificar una por una.
    """
    denuncias = db.execute(select(Denuncia)).scalars().all()
    for denuncia in denuncias:
        if verificar_codigo(codigo, denuncia.codigo_hash):
            return denuncia
    return None


@router.post(
    "",
    response_model=DenunciaVista,
    summary="Consultar un caso con el codigo de seguimiento",
)
def consultar(
    datos: SeguimientoConsulta, db: Session = Depends(get_db)
) -> DenunciaVista:
    # devuelve el estado del caso y el hilo de mensajes.
    # este no registra en la bitacora ,

    denuncia = buscar_por_codigo(db, datos.codigo)

    if denuncia is None:
        # respuesta identica exista o no el codigo
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Codigo no valido o caso inexistente"
        )
    mensajes = (
        db.execute(
            select(Mensaje)
            .where(Mensaje.denuncia_id == denuncia.id)
            .order_by(Mensaje.creado_en.asc())
        )
        .scalars()
        .all()
    )
    return DenunciaVista(
        denuncia_id=denuncia.id,
        estado=denuncia.estado,
        gravedad=denuncia.gravedad,
        categoria=denuncia.categoria.nombre,
        institucion=denuncia.institucion.nombre,
        relato=denuncia.relato,
        creado_en=denuncia.creado_en,
        mensajes=[
            MensajeVista(
                id=m.id,
                autor=m.autor,
                cuerpo=m.cuerpo,
                creado_en=m.creado_en,
            )
            for m in mensajes
        ],
    )


@router.post(
    "/mensajes",
    response_model=MensajeVista,
    status_code=status.HTTP_201_CREATED,
    summary="Escribir en el hilo del caso",
)
def escribir_mensaje(
    datos: MensajeCrear, db: Session = Depends(get_db)
) -> MensajeVista:
    # añade un mensaje al hilo, autenticando con el codigo

    denuncia = buscar_por_codigo(db, datos.codigo)
    if denuncia is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Codigo no valido o caso inexistente"
        )

    if denuncia.estado in ESTADOS_CERRADOS:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El caso esta cerrado y no admite mensajes nuevos",
        )

    mensaje = Mensaje(
        denuncia_id=denuncia.id,
        autor=AutorMensaje.DENUNCIANTE,
        cuerpo=datos.cuerpo,
    )
    db.add(mensaje)
    db.flush()

    cadena.registrar(
        db,
        TipoEvento.MENSAJE_AGREGADO,
        {
            "denuncia_id": denuncia.id,
            "mensaje_id": mensaje.id,
            "autor": AutorMensaje.DENUNCIANTE.value,
        },
    )

    return MensajeVista(
        id=mensaje.id,
        autor=mensaje.autor,
        cuerpo=mensaje.cuerpo,
        creado_en=mensaje.creado_en,
    )
