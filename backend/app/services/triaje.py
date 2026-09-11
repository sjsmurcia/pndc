"""Reglas de triaje y maquina de estados."""

from app.models.enums import DecisionRevision, EstadoDenuncia, Gravedad

# Transiciones permitidas. Lo que no esta aqui, no se puede hacer.
TRANSICIONES: dict[EstadoDenuncia, frozenset[EstadoDenuncia]] = {
    EstadoDenuncia.RECIBIDA: frozenset(
        {EstadoDenuncia.EN_SANEAMIENTO, EstadoDenuncia.EN_TRIAJE}
    ),
    EstadoDenuncia.EN_SANEAMIENTO: frozenset(
        {EstadoDenuncia.RECIBIDA, EstadoDenuncia.EN_TRIAJE}
    ),
    EstadoDenuncia.EN_TRIAJE: frozenset(
        {
            EstadoDenuncia.EN_REVISION_DOBLE,
            EstadoDenuncia.CRITICA,
            EstadoDenuncia.EN_REDACCION,
            EstadoDenuncia.RECHAZADA,
        }
    ),
    EstadoDenuncia.EN_REVISION_DOBLE: frozenset(
        {EstadoDenuncia.EN_REDACCION, EstadoDenuncia.ESCALADA}
    ),
    EstadoDenuncia.ESCALADA: frozenset(
        {EstadoDenuncia.EN_REDACCION, EstadoDenuncia.RECHAZADA}
    ),
    EstadoDenuncia.EN_REDACCION: frozenset(
        {EstadoDenuncia.EN_REDACCION, EstadoDenuncia.PUBLICADA}
    ),
    # Un caso critico se deriva y no vuelve: no existe camino a publicada.
    EstadoDenuncia.CRITICA: frozenset({EstadoDenuncia.DERIVADA}),
    # Estados finales.
    EstadoDenuncia.DERIVADA: frozenset(),
    EstadoDenuncia.PUBLICADA: frozenset(),
    EstadoDenuncia.RECHAZADA: frozenset(),
}

# Gravedades que exigen un segundo revisor antes de avanzar.
EXIGEN_DOBLE_REVISION = frozenset({Gravedad.ALTA})

# Gravedad que congela la publicacion y obliga a derivar.
CONGELA_PUBLICACION = Gravedad.CRITICA


class TransicionInvalida(Exception):
    """La transicion solicitada no esta permitida desde el estado actual."""


def puede_transicionar(
    desde: EstadoDenuncia, hacia: EstadoDenuncia
) -> bool:
    return hacia in TRANSICIONES.get(desde, frozenset())


def validar_transicion(desde: EstadoDenuncia, hacia: EstadoDenuncia) -> None:
    if not puede_transicionar(desde, hacia):
        raise TransicionInvalida(
            f"No se puede pasar de {desde.value} a {hacia.value}"
        )


def estado_tras_gravedad(gravedad: Gravedad) -> EstadoDenuncia:
    """Estado al que va un caso segun la gravedad asignada.

    Critica congela la publicacion: el caso se deriva a la autoridad y no
    llega al portal publico. Es la unica gravedad que decide el desenlace
    por si sola.
    """
    if gravedad == CONGELA_PUBLICACION:
        return EstadoDenuncia.CRITICA

    if gravedad in EXIGEN_DOBLE_REVISION:
        return EstadoDenuncia.EN_REVISION_DOBLE

    return EstadoDenuncia.EN_TRIAJE


def estado_tras_decision(
    estado_actual: EstadoDenuncia,
    decision: DecisionRevision,
    gravedad: Gravedad | None,
) -> EstadoDenuncia | None:
    """Estado resultante de una decision, o None si el caso no avanza.

    Devuelve None cuando la decision no cambia el estado: por ejemplo,
    solicitar ampliacion deja el caso donde esta a la espera de que el
    denunciante responda.
    """
    if decision == DecisionRevision.SOLICITA_AMPLIACION:
        return None

    if decision == DecisionRevision.RECHAZA:
        return EstadoDenuncia.RECHAZADA

    if decision == DecisionRevision.DERIVA:
        return EstadoDenuncia.CRITICA

    # PROCEDE: depende de la gravedad.
    if gravedad is None:
        raise TransicionInvalida(
            "Debe asignarse una gravedad antes de dar por procedente el caso"
        )

    if gravedad == CONGELA_PUBLICACION:
        return EstadoDenuncia.CRITICA

    if gravedad in EXIGEN_DOBLE_REVISION and estado_actual != (
        EstadoDenuncia.EN_REVISION_DOBLE
    ):
        return EstadoDenuncia.EN_REVISION_DOBLE

    return EstadoDenuncia.EN_REDACCION