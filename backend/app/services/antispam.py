"""Defensas contra envios automatizados.

NINGUNA IDENTIFICA A NADIE
Ese es el criterio que descarto reCAPTCHA: es un servicio de terceros que
recibiria la IP de cada visitante del formulario. Aqui todo se resuelve
dentro del propio portal.

TRES CAPAS
1. Honeypot: campo invisible para humanos. Si viene relleno, es un bot.
2. Prueba de trabajo: el navegador debe encontrar un nonce que produzca
   un hash con N ceros iniciales. Encarece el envio masivo sin molestar
   a quien denuncia una sola vez.
3. Rate limit efimero: contador en memoria que se pierde al reiniciar.
   Lo efimero es el punto: no queda registro de quien envio que.
"""

import hashlib
import hmac
import secrets
import time
from collections import deque

# Cada cero adicional multiplica por 16 el trabajo. Con 4 son unos 65 mil
# intentos: medio segundo en un movil, horas para mil envios.
CEROS_EXIGIDOS = 4

# Ventana de validez del reto. Corta para que un reto resuelto no se
# pueda reutilizar indefinidamente.
VIGENCIA_RETO = 600  # segundos

# Rate limit global del formulario. No es por persona: eso exigiria
# identificarla.
LIMITE_ENVIOS = 20
VENTANA_ENVIOS = 60  # segundos

# Secreto de proceso. Se regenera en cada arranque, asi que los retos
# emitidos antes de un reinicio dejan de ser validos. Es aceptable: se
# pide uno nuevo.
_SECRETO = secrets.token_bytes(32)

# Marcas de tiempo de los envios recientes. En memoria y acotado.
_envios: deque[float] = deque(maxlen=LIMITE_ENVIOS * 4)


class EnvioRechazado(Exception):
    """El envio no supera las defensas anti-spam."""


# --- Capa 1: honeypot ---


def honeypot_relleno(valor: str | None) -> bool:
    """El campo va oculto por CSS. Una persona no lo ve; un bot rellena
    todo lo que encuentra en el formulario."""
    return bool(valor and valor.strip())


# --- Capa 2: prueba de trabajo ---


def emitir_reto() -> dict:
    """Genera un reto firmado.

    La firma evita que alguien invente retos propios y resuelva uno
    trivial. El servidor no guarda nada: toda la informacion viaja en el
    reto y se valida por HMAC.
    """
    emitido = int(time.time())
    aleatorio = secrets.token_hex(16)
    material = f"{emitido}:{aleatorio}"
    firma = hmac.new(_SECRETO, material.encode(), hashlib.sha256).hexdigest()

    return {
        "reto": f"{material}:{firma}",
        "ceros": CEROS_EXIGIDOS,
        "vigencia_segundos": VIGENCIA_RETO,
    }


def _reto_valido(reto: str) -> bool:
    partes = reto.split(":")
    if len(partes) != 3:
        return False

    emitido, aleatorio, firma = partes

    esperada = hmac.new(
        _SECRETO, f"{emitido}:{aleatorio}".encode(), hashlib.sha256
    ).hexdigest()

    # compare_digest y no ==: comparar cadenas con == tarda mas o menos
    # segun cuantos caracteres coincidan, y eso filtra informacion.
    if not hmac.compare_digest(firma, esperada):
        return False

    try:
        return time.time() - int(emitido) <= VIGENCIA_RETO
    except ValueError:
        return False


def verificar_prueba(reto: str, nonce: str) -> None:
    """Comprueba que SHA256(reto + nonce) empiece por los ceros exigidos."""
    if not _reto_valido(reto):
        raise EnvioRechazado("El reto no es valido o ha caducado")

    digest = hashlib.sha256(f"{reto}{nonce}".encode()).hexdigest()
    if not digest.startswith("0" * CEROS_EXIGIDOS):
        raise EnvioRechazado("La prueba de trabajo no es correcta")


# --- Capa 3: rate limit efimero ---


def registrar_envio() -> None:
    """Anota un envio y rechaza si se supero el limite de la ventana.

    Solo se guardan marcas de tiempo. No hay IP, ni sesion, ni forma de
    saber si dos envios vienen de la misma persona: no es un limite POR
    persona, es un limite del formulario.
    """
    ahora = time.time()

    while _envios and ahora - _envios[0] > VENTANA_ENVIOS:
        _envios.popleft()

    if len(_envios) >= LIMITE_ENVIOS:
        raise EnvioRechazado(
            "El portal esta recibiendo demasiados envios. "
            "Espere un momento e intentelo de nuevo."
        )

    _envios.append(ahora)


def reiniciar_contador() -> None:
    """Limpia el contador. Solo para pruebas."""
    _envios.clear()