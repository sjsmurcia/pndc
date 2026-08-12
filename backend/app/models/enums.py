import enum


class TipoInstitucion(str, enum.Enum):
    """clasificacion de las instituciones, basado en la estructura de la
    administracion public: centralizada, descentralizada, reguladora, empresas
    publicas, gobiernos locales y poderes del estado. tambien con el sector privado, porque
    la mayoria de casos hay un proveedor y un comprador"""

    SECRETARIA_ESTADO = "secretaria_estado"
    INSTITUCION_DESCENTRALIZADA = "institucion_descentralizada"
    ENTE_REGULADOR = "ente_regulador"
    EMPRESA_PUBLICA = "empresa_publica"
    MUNICIPALIDAD = "municipalidad"
    PODER_JUDICIAL = "poder_judicial"
    ORGANO_CONTROL = "organo_control"
    EMPRESA_PRIVADA = "empresa_privada"
    OTRO = "otro"


class NivelIdentidad(str, enum.Enum):
    """lo elige quien denuncia."""

    ANONIMO = "anonimo"
    SEUDONIMO = "seudonimo"
    PUBLICO = "publico"


class Gravedad(str, enum.Enum):
    """la asigna el revisor en el triaje"""

    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoDenuncia(str, enum.Enum):
    """ciclo de vida"""

    RECIBIDA = "recibida"
    EN_SANEAMIENTO = "en_saneamiento"
    EN_TRIAJE = "en_triaje"
    EN_REVISION_DOBLE = "en_revision_doble"
    ESCALADA = "escalada"
    EN_REDACCION = "en_redaccion"
    CRITICA = "critica"
    DERIVADA = "derivada"
    PUBLICADA = "publicada"
    RECHAZADA = "rechazada"


class AutorMensaje(str, enum.Enum):
    """quien escribe el mensaje no hay identidad solo el lado dialogo"""

    DENUNCIANTE = "denunciante"
    REVISOR = "revisor"


class RolRevisor(str, enum.Enum):
    """Los designa la organizacion que opera el portal, no se eligen entre
    los usuarios. El supervisor resuelve desacuerdos y aprueba casos
    graves."""

    REVISOR = "revisor"
    SUPERVISOR = "supervisor"


class DecisionRevision(str, enum.Enum):
    """Resultado del triaje de un revisor sobre una denuncia."""

    PROCEDE = "procede"
    RECHAZA = "rechaza"
    SOLICITA_AMPLIACION = "solicita_ampliacion"
    DERIVA = "deriva"
