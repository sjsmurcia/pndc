from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import AutorMensaje, EstadoDenuncia, Gravedad, NivelIdentidad


class DenunciaCrear(BaseModel):
    # lo que envia la denuncia

    categoria_id: int
    institucion_id: int
    nivel_identidad: NivelIdentidad = NivelIdentidad.ANONIMO
    relato: str = Field(min_length=40, max_length=20000)

    # prueba de trabajo.
    nonce: str | None = None
    #navegador
    reto: str | None=None
    
    # campo trampa
    sitio_web: str | None = None


class DenunciaCreada(BaseModel):
    # respuesta del alta el codigo en claro viaja una sola vez

    denuncia_id: int
    codigo: str
    estado: EstadoDenuncia
    creado_en: datetime
    advertencia: str = (
        "Guarde este codigo ahora. Es la unica forma de dar Seguimiento "
        "a su caso y no puede recuperarse si lo pierde. "
    )


class SeguimientoConsulta(BaseModel):
    # acceso al caso con el codigo de seguimiento

    codigo: str = Field(min_length=8, max_length=40)


class MensajeVista(BaseModel):
    # un mensaje del hilo, como lo ve quien denuncia

    id: int
    autor: AutorMensaje
    cuerpo: str
    creado_en: datetime


class DenunciaVista(BaseModel):
    # estado del caso. no incluye el codigo ni su hash
    denuncia_id: int
    estado: EstadoDenuncia
    gravedad: Gravedad | None
    categoria: str
    institucion: str
    relato: str
    creado_en: datetime
    mensajes: list[MensajeVista] = []

class MensajeCrear(BaseModel):
    #mensaje que envia quien denuncia, login con su codigo 

    codigo: str=Field(min_length=8, max_length=40)
    cuerpo: str=Field(min_length=5, max_length=5000)

class EvidenciaSubida(BaseModel):
    #resultado del saneamiento de una imagen
    evidencia_id:int
    mime:str
    sha256:str
    ancho:int
    alto:int
    sanitizada:bool
    aviso:str=(
        "El saneamiento elimina lo que el archivo guarda sobre usted, no lo "
        "que el archivo muestra. Si en la imagen aparece su escritorio, su "
        "firma o algo que lo identifique, revisela antes de continuar."
        
    )