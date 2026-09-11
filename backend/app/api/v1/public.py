from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.integridad import Bitacora
from app.services.cadena import verificar_cadena

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