from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.integridad import Bitacora
from app.services.cadena import verificar_cadena
from app.models.catalogo import Categoria, Institucion
from app.models.denuncia import Denuncia
from app.models.desenlace import Publicacion
from app.models.enums import EstadoDenuncia
router = APIRouter(prefix="/publico", tags=["publico"])


@router.get(
    "/bitacora",
    summary="Registro de integridad completo",
)
def exportar_bitacora(
    desde: int = Query(default=1, ge=1),
    limite: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict:
    """Devuelve la cadena de eventos para que cualquiera la verifique.

    Publico y sin autenticacion a proposito: un registro que solo puede
    auditar quien opera el portal no prueba nada. Los payloads no
    contienen datos identificatorios, y hay una prueba automatizada que
    lo garantiza (ver test_auditoria_identidad.py).
    """
    eventos = (
        db.execute(
            select(Bitacora)
            .where(Bitacora.indice >= desde)
            .order_by(Bitacora.indice.asc())
            .limit(limite)
        )
        .scalars()
        .all()
    )

    total = db.execute(select(func.count(Bitacora.indice))).scalar_one()

    return {
        "total": total,
        "desde": desde,
        "devueltos": len(eventos),
        "eventos": [
            {
                "indice": e.indice,
                "tipo_evento": e.tipo_evento,
                "payload": e.payload,
                "hash_anterior": e.hash_anterior,
                "hash_actual": e.hash_actual,
                "creado_en": e.creado_en.isoformat(),
            }
            for e in eventos
        ],
    }


@router.get(
    "/bitacora/estado",
    summary="Estado de integridad de la cadena",
)
def estado_cadena(db: Session = Depends(get_db)) -> dict:
    """Verifica la cadena y reporta si esta intacta.

    Que el propio portal diga que su cadena esta bien no prueba nada: por
    eso existe el verificador independiente. Esto es un indicador rapido,
    no una garantia, y se declara asi.
    """
    intacta, indice_roto = verificar_cadena(db)
    total = db.execute(select(func.count(Bitacora.indice))).scalar_one()

    return {
        "intacta": intacta,
        "eventos": total,
        "indice_roto": indice_roto,
        "advertencia": (
            "Esta comprobacion la hace el propio portal. Para una "
            "verificacion independiente, descargue el registro y use el "
            "verificador con un rol de solo lectura."
        ),
    }
@router.get(
    "/casos",
    summary="Casos publicados",
)
def casos_publicados(
    limite: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Lista las versiones redactadas de los casos publicados.

    Devuelve el texto redactado, nunca el relato original: el primero lo
    escribio un revisor eliminando lo que identificaria a terceros; el
    segundo es lo que escribio quien denuncio.
    """
    filas = db.execute(
        select(Publicacion, Denuncia)
        .join(Denuncia, Denuncia.id == Publicacion.denuncia_id)
        .where(Denuncia.estado == EstadoDenuncia.PUBLICADA)
        .order_by(Publicacion.creado_en.desc())
        .limit(limite)
    ).all()

    return [
        {
            "caso_id": publicacion.denuncia_id,
            "categoria": denuncia.categoria.nombre,
            "institucion": denuncia.institucion.nombre,
            "tipo_institucion": denuncia.institucion.tipo.value,
            "gravedad": denuncia.gravedad.value if denuncia.gravedad else None,
            "texto": publicacion.texto_redactado,
            "publicado_en": publicacion.creado_en.isoformat(),
        }
        for publicacion, denuncia in filas
    ]


@router.get(
    "/ranking",
    summary="Denuncias publicadas por institucion y categoria",
)
def ranking(db: Session = Depends(get_db)) -> dict:
    """Conteo de casos PUBLICADOS, no de denuncias recibidas.

    Contar lo recibido permitiria que cualquiera inflara la posicion de
    una institucion enviando denuncias falsas. Solo cuenta lo que un
    revisor aprobo y un supervisor publico.
    """
    por_institucion = db.execute(
        select(
            Institucion.nombre,
            Institucion.tipo,
            func.count(Denuncia.id).label("casos"),
        )
        .join(Denuncia, Denuncia.institucion_id == Institucion.id)
        .where(Denuncia.estado == EstadoDenuncia.PUBLICADA)
        .group_by(Institucion.id, Institucion.nombre, Institucion.tipo)
        .order_by(func.count(Denuncia.id).desc())
    ).all()

    por_categoria = db.execute(
        select(Categoria.nombre, func.count(Denuncia.id).label("casos"))
        .join(Denuncia, Denuncia.categoria_id == Categoria.id)
        .where(Denuncia.estado == EstadoDenuncia.PUBLICADA)
        .group_by(Categoria.id, Categoria.nombre)
        .order_by(func.count(Denuncia.id).desc())
    ).all()

    return {
        # El titulo va en la respuesta, no solo en la interfaz: es una
        # decision de contenido y debe viajar con los datos.
        "titulo": "Denuncias publicadas por institucion",
        "aclaracion": (
            "Este conteo refleja cuantos casos fueron publicados tras ser "
            "revisados, no que las instituciones senaladas hayan cometido "
            "irregularidad alguna. Las denuncias no estan verificadas "
            "judicialmente."
        ),
        "instituciones": [
            {"nombre": nombre, "tipo": tipo.value, "casos": casos}
            for nombre, tipo, casos in por_institucion
        ],
        "categorias": [
            {"nombre": nombre, "casos": casos}
            for nombre, casos in por_categoria
        ],
    }