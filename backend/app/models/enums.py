import enum


class TipoInstitucion(str, enum.Enum):
    """clasificacion de las instituciones, basado en la estructura de la 
    administracion public: centralizada, descentralizada, reguladora, empresas 
    publicas, gobiernos locales y poderes del estado. tambien con el sector privado, porque
    la mayoria de casos hay un proveedor y un comprador """

    SECRETARIA_ESTADO ="secretaria_estado"
    INSTITUCION_DESCENTRALIZADA = "institucion_descentralizada"
    ENTE_REGULADOR = "ente_regulador"
    EMPRESA_PUBLICA = "empresa_publica"
    MUNICIPALIDAD = "municipalidad"
    PODER_JUDICIAL = "poder_judicial"
    ORGANO_CONTROL = "organo_control"
    EMPRESA_PRIVADA = "empresa_privada"
    OTRO = "otro"
