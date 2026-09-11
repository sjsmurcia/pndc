from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencias import revisor_actual
from app.db.session import get_db
from app.models.denuncia import Denuncia

from app.models.evidencia import Evidencia, Mensaje

from app.schemas.revision import (
    CasoDetalle,
    CasoEnCola,
    DecisionEmitir,
    EvidenciaEnCaso,
    GravedadAsignar,
    MensajeEnCaso,
    ResultadoDecision,
)
from app.services import cadena
from app.services.eventos import TipoEvento
from app.services.triaje import (
    TransicionInvalida,
    estado_tras_decision,
    estado_tras_gravedad,
    validar_transicion,
)


from app.services.triaje import EXIGEN_DOBLE_REVISION

from app.models.enums import AutorMensaje, DecisionRevision, EstadoDenuncia, Gravedad
from app.models.revision import AsignacionRevision, Revision, Revisor

from pathlib import Path

from fastapi import Response

from app.api.v1.denuncias import DIR_EVIDENCIAS
from app.models.integridad import DescargaEvidencia
from app.schemas.revision import DescargaSolicitud
from app.services.marca import MarcadoFallido, marcar_copia
from app.api.dependencias import revisor_actual, supervisor_actual
from app.models.desenlace import Publicacion
from app.schemas.revision import PublicacionVista,RedaccionGuardar
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
            select(func.count(Evidencia.id)).where(Evidencia.denuncia_id == denuncia.id)
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

    db.add(AsignacionRevision(denuncia_id=denuncia_id, revisor_id=revisor.id))

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


def _caso_asignado(db: Session, denuncia_id: int, revisor: Revisor) -> Denuncia:
    """Recupera un caso comprobado que el revisor tenga asignado"""
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
            status.HTTP_403_FORBIDDEN, "Debe tomar el caso antes de actuar sobre el"
        )
    return denuncia


@router.post(
    "/casos/{denuncia_id}/gravedad",
    response_model=ResultadoDecision,
    summary="Asignar gravedad a un caso",
)
def asignar_gravedad(
    denuncia_id: int,
    datos: GravedadAsignar,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> ResultadoDecision:
    """Clasifica el caso y mueve su estado segun la regla de gravedad.

    Critica congela la publicacion de inmediato: el caso no puede llegar
    al portal publico, solo derivarse.
    """
    denuncia = _caso_asignado(db, denuncia_id, revisor)

    denuncia.gravedad = datos.gravedad
    destino = estado_tras_gravedad(datos.gravedad)

    if destino != denuncia.estado:
        try:
            validar_transicion(denuncia.estado, destino)
        except TransicionInvalida as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        denuncia.estado = destino

    cadena.registrar(
        db,
        TipoEvento.GRAVEDAD_ASIGNADA,
        {
            "denuncia_id": denuncia_id,
            "revisor_id": revisor.id,
            "gravedad": datos.gravedad.value,
        },
    )

    mensajes = {
        Gravedad.CRITICA: (
            "Caso critico: la publicacion queda congelada. Debe derivarse "
            "a la autoridad competente."
        ),
        Gravedad.ALTA: (
            "Caso grave: requiere la coincidencia de un segundo revisor "
            "antes de avanzar."
        ),
    }

    return ResultadoDecision(
        denuncia_id=denuncia_id,
        estado=denuncia.estado,
        gravedad=denuncia.gravedad,
        revisiones=_contar_revisiones(db, denuncia_id),
        mensaje=mensajes.get(datos.gravedad, "Gravedad registrada."),
    )


def _contar_revisiones(db: Session, denuncia_id: int) -> int:
    return db.execute(
        select(func.count(Revision.id)).where(Revision.denuncia_id == denuncia_id)
    ).scalar_one()


@router.post(
    "/casos/{denuncia_id}/decision",
    response_model=ResultadoDecision,
    summary="Emitir decision sobre un caso",
)
def emitir_decision(
    denuncia_id: int,
    datos: DecisionEmitir,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> ResultadoDecision:
    """Registra la decision del revisor y avanza el caso si procede.

    En gravedad alta el caso no avanza con una sola decision: se exige
    que un segundo revisor coincida. Si discrepan, escala al supervisor.
    """
    denuncia = _caso_asignado(db, denuncia_id, revisor)

    ya_decidio = db.execute(
        select(Revision).where(
            Revision.denuncia_id == denuncia_id,
            Revision.revisor_id == revisor.id,
        )
    ).scalar_one_or_none()

    if ya_decidio is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya emitio una decision sobre este caso",
        )

    db.add(
        Revision(
            denuncia_id=denuncia_id,
            revisor_id=revisor.id,
            decision=datos.decision,
            notas=datos.notas,
        )
    )
    db.flush()

    # La asignacion queda completada: este revisor ya hizo su trabajo.
    asignacion = db.execute(
        select(AsignacionRevision).where(
            AsignacionRevision.denuncia_id == denuncia_id,
            AsignacionRevision.revisor_id == revisor.id,
        )
    ).scalar_one()
    asignacion.completada = True

    cadena.registrar(
        db,
        TipoEvento.REVISION_EMITIDA,
        {
            "denuncia_id": denuncia_id,
            "revisor_id": revisor.id,
            "decision": datos.decision.value,
        },
    )

    decisiones = (
        db.execute(select(Revision).where(Revision.denuncia_id == denuncia_id))
        .scalars()
        .all()
    )

    mensaje, destino = _resolver_avance(denuncia, decisiones)

    if destino is not None and destino != denuncia.estado:
        try:
            validar_transicion(denuncia.estado, destino)
        except TransicionInvalida as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

        denuncia.estado = destino

        if destino == EstadoDenuncia.ESCALADA:
            cadena.registrar(
                db,
                TipoEvento.CASO_ESCALADO,
                {
                    "denuncia_id": denuncia_id,
                    "revisor_id": revisor.id,
                    "motivo": "Los revisores no coinciden en la decision",
                },
            )
        elif destino == EstadoDenuncia.RECHAZADA:
            cadena.registrar(
                db,
                TipoEvento.CASO_RECHAZADO,
                {"denuncia_id": denuncia_id, "revisor_id": revisor.id},
            )

    return ResultadoDecision(
        denuncia_id=denuncia_id,
        estado=denuncia.estado,
        gravedad=denuncia.gravedad,
        revisiones=len(decisiones),
        mensaje=mensaje,
    )


def _resolver_avance(
    denuncia: Denuncia, decisiones: list[Revision]
) -> tuple[str, EstadoDenuncia | None]:
    """Decide si el caso avanza y a donde.

    Es la regla del doble revisor: en gravedad alta hacen falta dos
    decisiones coincidentes. Una sola no basta, y dos distintas escalan.
    """
    ultima = decisiones[-1]

    if ultima.decision == DecisionRevision.SOLICITA_AMPLIACION:
        return (
            "Solicitud registrada. El caso espera respuesta del denunciante.",
            None,
        )

    exige_doble = denuncia.gravedad in EXIGEN_DOBLE_REVISION

    if exige_doble and len(decisiones) < 2:
        return (
            "Decision registrada. Este caso es grave y requiere que un "
            "segundo revisor coincida antes de avanzar.",
            None,
        )

    if exige_doble:
        distintas = {d.decision for d in decisiones[-2:]}
        if len(distintas) > 1:
            return (
                "Los revisores no coinciden. El caso escala a un supervisor.",
                EstadoDenuncia.ESCALADA,
            )

    destino = estado_tras_decision(denuncia.estado, ultima.decision, denuncia.gravedad)

    textos = {
        EstadoDenuncia.RECHAZADA: "Caso rechazado y archivado.",
        EstadoDenuncia.CRITICA: (
            "Caso critico: la publicacion queda congelada y debe derivarse."
        ),
        EstadoDenuncia.EN_REDACCION: (
            "Caso aprobado. Pasa a redaccion de la version publicable."
        ),
    }

    return textos.get(destino, "Decision registrada."), destino


@router.post(
    "/evidencias/{evidencia_id}/descarga",
    summary="Descargar una copia marcada de la evidencia",
)
def descargar_evidencia(
    evidencia_id: int,
    datos: DescargaSolicitud,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> Response:
    """Entrega una copia unica marcada y registra la descarga.

    La justificacion es obligatoria: si un revisor tiene que escribir por
    que necesita el archivo, la descarga por curiosidad deja de ser
    gratuita. Y si la copia se filtra, marca_id dice cual de todas fue.
    """
    evidencia = db.get(Evidencia, evidencia_id)
    if evidencia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidencia inexistente")

    # Solo quien tiene el caso asignado puede descargar su evidencia.
    _caso_asignado(db, evidencia.denuncia_id, revisor)

    ruta = DIR_EVIDENCIAS / Path(evidencia.url).name
    if not ruta.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El archivo no esta disponible")

    try:
        copia = marcar_copia(ruta.read_bytes(), evidencia.mime)
    except MarcadoFallido as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    db.add(
        DescargaEvidencia(
            evidencia_id=evidencia_id,
            revisor_id=revisor.id,
            justificacion=datos.justificacion,
            marca_id=copia.marca_id,
            sha256_copia=copia.sha256,
        )
    )
    db.flush()

    cadena.registrar(
        db,
        TipoEvento.EVIDENCIA_DESCARGADA,
        {
            "evidencia_id": evidencia_id,
            "revisor_id": revisor.id,
            "marca_id": str(copia.marca_id),
            "sha256_copia": copia.sha256,
        },
    )

    # PNG siempre: la marca vive en los pixeles y JPEG la destruiria al
    # recomprimir.
    extension = "png" if evidencia.mime != "application/pdf" else "pdf"
    tipo = "image/png" if extension == "png" else "application/pdf"

    return Response(
        content=copia.contenido,
        media_type=tipo,
        headers={
            "Content-Disposition": (
                f'attachment; filename="evidencia-{evidencia_id}.{extension}"'
            ),
            # Marca visible en la cabecera: el revisor sabe que su copia
            # esta identificada. La disuasion funciona mejor si se sabe.
            "X-PNDC-Marca": str(copia.marca_id),
        },
    )
@router.put(
    "/casos/{denuncia_id}/redaccion",
    response_model=PublicacionVista,
    summary="Guardar la version publicable",
)
def guardar_redaccion(
    denuncia_id: int,
    datos: RedaccionGuardar,
    revisor: Revisor = Depends(revisor_actual),
    db: Session = Depends(get_db),
) -> PublicacionVista:
    """Crea o actualiza el texto redactado. No publica nada.

    Guardar y publicar son acciones distintas a proposito: quien redacta
    no decide que se hace publico.
    """
    denuncia = _caso_asignado(db, denuncia_id, revisor)

    if denuncia.estado != EstadoDenuncia.EN_REDACCION:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"El caso esta en estado {denuncia.estado.value} y no admite "
            "redaccion",
        )

    publicacion = db.execute(
        select(Publicacion).where(Publicacion.denuncia_id == denuncia_id)
    ).scalar_one_or_none()

    if publicacion is None:
        publicacion = Publicacion(
            denuncia_id=denuncia_id,
            texto_redactado=datos.texto_redactado,
        )
        db.add(publicacion)
    else:
        publicacion.texto_redactado = datos.texto_redactado

    db.flush()

    return PublicacionVista(
        denuncia_id=denuncia_id,
        publicacion_id=publicacion.id,
        estado=denuncia.estado,
        texto_redactado=publicacion.texto_redactado,
        publicado=False,
        creado_en=publicacion.creado_en,
    )


@router.post(
    "/casos/{denuncia_id}/publicar",
    response_model=PublicacionVista,
    summary="Aprobar y publicar un caso",
)
def publicar_caso(
    denuncia_id: int,
    supervisor: Revisor = Depends(supervisor_actual),
    db: Session = Depends(get_db),
) -> PublicacionVista:
    """Publica el caso. Solo un supervisor puede hacerlo.

    Quien redacta no publica: separar la escritura de la autorizacion es
    el mismo principio que el doble revisor en casos graves.
    """
    denuncia = db.get(Denuncia, denuncia_id)
    if denuncia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Caso inexistente")

    publicacion = db.execute(
        select(Publicacion).where(Publicacion.denuncia_id == denuncia_id)
    ).scalar_one_or_none()

    if publicacion is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No hay version redactada que publicar",
        )

    try:
        validar_transicion(denuncia.estado, EstadoDenuncia.PUBLICADA)
    except TransicionInvalida as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    denuncia.estado = EstadoDenuncia.PUBLICADA

    cadena.registrar(
        db,
        TipoEvento.CASO_PUBLICADO,
        {
            "denuncia_id": denuncia_id,
            "revisor_id": supervisor.id,
            "publicacion_id": publicacion.id,
        },
    )

    return PublicacionVista(
        denuncia_id=denuncia_id,
        publicacion_id=publicacion.id,
        estado=denuncia.estado,
        texto_redactado=publicacion.texto_redactado,
        publicado=True,
        creado_en=publicacion.creado_en,
    )