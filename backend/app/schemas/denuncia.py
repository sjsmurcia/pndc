from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import EstadoDenuncia, NivelIdentidad

class DenunciaCrear(BaseModel):
    #lo que envia la denuncia 

    categoria_id: int 
    institucion_id: int
    nivel_identidad: NivelIdentidad = NivelIdentidad.ANONIMO
    relato:str =Field(min_length=40, max_length=20000)

    #prueba de trabajo. 
    nonce:str | None = None

    #campo trampa
    sitio_web:str | None=None


class DenunciaCreada(BaseModel):
    #respuesta del alta el codigo en claro viaja una sola vez 

    denuncia_id:int
    codigo:str
    estado:EstadoDenuncia
    creado_en:datetime
    advertencia:str =(
        "Guarde este codigo ahora. Es la unica forma de dar Seguimiento "
        "A su caso y no puede recuperarse si lo pierde. "
    )