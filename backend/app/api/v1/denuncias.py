from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select 
from sqlalchemy.orm import Session 

from app.db.session import get_db
from app.models.catalogo import Categoria, Institucion
from app.models.denuncia import Denuncia
from app.models.enums import EstadoDenuncia
from app.schemas.denuncia import DenunciaCreada, DenunciaCrear
from app.services import cadena
from app.services.codigo import generar_codigo, hashear_codigo
from app.services.eventos import TipoEvento

router = APIRouter(prefix="/denuncias", tags=["denuncias"])

@router.post(
    "",
    response_model=DenunciaCreada, 
    status_code=status.HTTP_201_CREATED,
    summary="Crear una denuncia anonima",
)

def crear_denuncia(
    datos: DenunciaCrear, db:Session=Depends(get_db)
)->DenunciaCreada:
    #registra una denuncia y emite el codigo del seguimiento. 

    if not db.get(Categoria, datos.categoria_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria Inexistente")
    if not db.get(Institucion, datos.institucion_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Institucion inexistente"

        )
    codigo=generar_codigo()

    denuncia = Denuncia(
        codigo_hash = hashear_codigo(codigo),
        categoria_id=datos.categoria_id,
        institucion_id=datos.institucion_id,
        nivel_identidad=datos.nivel_identidad,
        estado=EstadoDenuncia.RECIBIDA,
        relato=datos.relato,
    )
    db.add(denuncia)
    db.flush() #asignar el id sin cerrar la transaccion 

    #el evento entra en la misma transaccion. si el alta falla la bitacora falla 

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

