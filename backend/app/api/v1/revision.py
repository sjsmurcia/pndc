from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencias import revisor_actual
from app.db.session import get_db
from app.models.denuncia import Denuncia
from app.models.enums import AutorMensaje, EstadoDenuncia
from app.models.evidencia import Evidencia, Mensaje
from app.models.revision import AsignacionRevision, Revisor
from app.schemas.revision import (
    CasoDetalle,
    CasoEnCola,
    EvidenciaEnCaso,
    MensajeEnCaso,
)
from app.services import cadena
from app.services.eventos import TipoEvento

router = APIRouter(prefix="/revision", tags=["revision"])

# Estados que siguen en la cola. Los desenlaces quedan fuera.
EN_PROCESO = (
    EstadoDenuncia.RECIBIDA,
    EstadoDenuncia.EN_TRIAJE,
    EstadoDenuncia.EN_REVISION_DOBLE,
    EstadoDenuncia.ESCALADA,
    EstadoDenuncia.EN_REDACCION,
)


@router.get(
    "/cola",
    response_model=list[CasoEnCola],
    summary="Casos pendientes de revision",
)
def cola_de_triaje(
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> list[CasoEnCola]:
    """Lista los casos en proceso, sin el relato.

    Devolver el contenido aqui permitiria a un revisor leer todos los
    casos sin dejar rastro. El relato exige abrir el caso, y abrirlo
    exige tomarlo.
    """
    denuncias = (
        db.execute(
            select(Denuncia)
            .where(Denuncia.estado.in_(EN_PROCESO))
            .order_by(Denuncia.creado_en.asc())
        )
        .scalars()
        .all()
    )

    mias = set(
        db.execute(
            select(AsignacionRevision.denuncia_id).where(
                AsignacionRevision.revisor_id == revisor.id
            )
        )
        .scalars()
        .all()
    )

    resultado = []
    for denuncia in denuncias:
        evidencias = db.execute(
            select(func.count(Evidencia.id)).where(
                Evidencia.denuncia_id == denuncia.id
            )
        ).scalar_one()

        # "Sin leer" para el revisor = mensajes del denunciante. No hay
        # marca de lectura porque eso exigiria registrar cada apertura.
        del_denunciante = db.execute(
            select(func.count(Mensaje.id)).where(
                Mensaje.denuncia_id == denuncia.id,
                Mensaje.autor == AutorMensaje.DENUNCIANTE,
            )
        ).scalar_one()

        resultado.append(
            CasoEnCola(
                denuncia_id=denuncia.id,
                estado=denuncia.estado,
                gravedad=denuncia.gravedad,
                categoria=denuncia.categoria.nombre,
                institucion=denuncia.institucion.nombre,
                nivel_identidad=denuncia.nivel_identidad,
                seudonimo=denuncia.seudonimo,
                evidencias=evidencias,
                mensajes_sin_leer=del_denunciante,
                creado_en=denuncia.creado_en,
                asignado_a_mi=denuncia.id in mias,
            )
        )

    return resultado


@router.post(
    "/casos/{denuncia_id}/tomar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Tomar un caso para revisarlo",
)
def tomar_caso(
    denuncia_id: int,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> None:
    """Asigna el caso al revisor y lo registra en la bitacora.

    Es el punto donde la rendicion de cuentas empieza: a partir de aqui
    consta publicamente que este revisor accedio a este caso.
    """
    denuncia = db.get(Denuncia, denuncia_id)
    if denuncia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Caso inexistente")

    ya_asignado = db.execute(
        select(AsignacionRevision).where(
            AsignacionRevision.denuncia_id == denuncia_id,
            AsignacionRevision.revisor_id == revisor.id,
        )
    ).scalar_one_or_none()

    if ya_asignado is not None:
        return  # idempotente: tomar dos veces no duplica ni falla

    db.add(
        AsignacionRevision(denuncia_id=denuncia_id, revisor_id=revisor.id)
    )

    if denuncia.estado == EstadoDenuncia.RECIBIDA:
        denuncia.estado = EstadoDenuncia.EN_TRIAJE

    cadena.registrar(
        db,
        TipoEvento.REVISOR_ASIGNADO,
        {"denuncia_id": denuncia_id, "revisor_id": revisor.id},
    )


@router.get(
    "/casos/{denuncia_id}",
    response_model=CasoDetalle,
    summary="Detalle de un caso asignado",
)
def detalle_caso(
    denuncia_id: int,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> CasoDetalle:
    """Contenido completo. Exige tener el caso asignado."""
    denuncia = db.get(Denuncia, denuncia_id)
    if denuncia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Caso inexistente")

    asignado = db.execute(
        select(AsignacionRevision).where(
            AsignacionRevision.denuncia_id == denuncia_id,
            AsignacionRevision.revisor_id == revisor.id,
        )
    ).scalar_one_or_none()

    if asignado is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Debe tomar el caso antes de ver su contenido",
        )

    evidencias = (
        db.execute(
            select(Evidencia)
            .where(Evidencia.denuncia_id == denuncia_id)
            .order_by(Evidencia.id)
        )
        .scalars()
        .all()
    )

    mensajes = (
        db.execute(
            select(Mensaje)
            .where(Mensaje.denuncia_id == denuncia_id)
            .order_by(Mensaje.creado_en)
        )
        .scalars()
        .all()
    )

    asignados = (
        db.execute(
            select(Revisor.nombre)
            .join(
                AsignacionRevision,
                AsignacionRevision.revisor_id == Revisor.id,
            )
            .where(AsignacionRevision.denuncia_id == denuncia_id)
        )
        .scalars()
        .all()
    )

    return CasoDetalle(
        denuncia_id=denuncia.id,
        estado=denuncia.estado,
        gravedad=denuncia.gravedad,
        categoria=denuncia.categoria.nombre,
        institucion=denuncia.institucion.nombre,
        nivel_identidad=denuncia.nivel_identidad,
        seudonimo=denuncia.seudonimo,
        relato=denuncia.relato,
        creado_en=denuncia.creado_en,
        evidencias=[
            EvidenciaEnCaso(
                evidencia_id=e.id,
                mime=e.mime,
                sha256=e.sha256,
                sanitizada=e.sanitizada,
                creado_en=e.creado_en,
            )
            for e in evidencias
        ],
        mensajes=[
            MensajeEnCaso(
                id=m.id,
                autor=m.autor.value,
                cuerpo=m.cuerpo,
                creado_en=m.creado_en,
            )
            for m in mensajes
        ],
        revisores_asignados=list(asignados),
    )