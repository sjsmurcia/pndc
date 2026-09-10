# generacion y verificacion del codigo de seguimiento

import secrets
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# sin caracteres ambiguos

ALFABETO = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

PREFIJO = "PNDC"
GRUPOS = 3
LONGITUD_GRUPO = 4

# argon2id con los parametros por defecto de la libreria, que siguen las
# recomendaciones de rfc 9016 no se ajustan a mano elegir parametros
# criptograficos por intuicion es como escribir criptografia propia

_hasher = PasswordHasher()


def generar_codigo() -> str:
    # codigo nuevo, con modulo secrets y no con random
    grupos = [
        "".join(secrets.choice(ALFABETO) for _ in range(LONGITUD_GRUPO))
        for _ in range(GRUPOS)
    ]
    return "-".join([PREFIJO, *grupos])


def hashear_codigo(codigo: str) -> str:
    # hash argon2 del codigo
    return _hasher.hash(normalizar(codigo))


def verificar_codigo(codigo: str, hash_guardado: str) -> bool:
    # comprueba un codigo contra su hash
    try:
        return _hasher.verify(hash_guardado, normalizar(codigo))
    except (VerifyMismatchError, InvalidHashError):
        return False


def normalizar(codigo: str) -> str:
    # tolera como la gente escribe de verdad minusculas, espacios de mas guiones
    limpio = codigo.strip().upper().replace(" ", "").replace("-", "")
    return limpio


#palabras neutras para el suedonimo. lo genera el sistema 

_ADJETIVOS = (
    "Atento", "Breve", "Cauto", "Directo", "Firme", "Lucido",
    "Paciente", "Preciso", "Prudente", "Sereno", "Sobrio", "Tenaz",
)

_SUSTANTIVOS = (
    "Testigo", "Observador", "Informante", "Vigia", "Contador",
    "Registro", "Reporte", "Aviso", "Senal", "Indicio",
)


def generar_seudonimo() -> str:
    """Seudonimo legible para el panel de revision.

    Sirve para que un revisor pueda decir "el caso de Testigo Sereno 47"
    en vez de recitar un numero. No aporta ninguna informacion sobre la
    persona: se genera con secrets y no guarda relacion con el codigo.
    """
    adjetivo = secrets.choice(_ADJETIVOS)
    sustantivo = secrets.choice(_SUSTANTIVOS)
    numero = secrets.randbelow(900) + 100
    return f"{sustantivo} {adjetivo} {numero}"