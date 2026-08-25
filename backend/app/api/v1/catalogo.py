from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.catalogo import Categoria, Institucion
from app.schemas.catalogo import Catalogo, CategoriaVista, InstitucionVista

router = APIRouter(prefix="/catalogo", tags=["catalogo"])


@router.get(
    "",
    response_model=Catalogo,
    summary="Categorias e instituciones disponibles",
)
def obtener_catalogo(db: Session = Depends(get_db)) -> Catalogo:
    """Datos publicos: quien va a denunciar aun no tiene codigo, asi que
    este endpoint no puede exigir autenticacion de ningun tipo.

    No emite evento a la bitacora: consultar el catalogo no es un hecho
    del caso, y registrarlo permitiria inferir cuanta gente abre el
    formulario sin llegar a enviarlo.
    """
    categorias = (
        db.execute(select(Categoria).order_by(Categoria.nombre)).scalars().all()
    )
    instituciones = (
        db.execute(select(Institucion).order_by(Institucion.nombre))
        .scalars()
        .all()
    )

    return Catalogo(
        categorias=[CategoriaVista(id=c.id, nombre=c.nombre) for c in categorias],
        instituciones=[
            InstitucionVista(id=i.id, nombre=i.nombre, tipo=i.tipo)
            for i in instituciones
        ],
    )