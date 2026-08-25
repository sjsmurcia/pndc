from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# La aplicacion se conecta con pndc_app, el rol restringido. Nunca con
# pndc_owner: ese es solo para migraciones.
engine = create_engine(settings.database_url, pool_pre_ping=True, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesion por peticion.

    El commit va al final y solo si no hubo excepcion. Asi la denuncia y
    su evento de bitacora entran juntos o no entra ninguno.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()