##Catalogo de eventos de la bitacora.

# regla que manda sobre todo el archivo
# ninguno de los playloas puede tener
# -el codigo de seguimiento
# -el relato de la denuncia ni el cuerpo de un mensaje
# - direcciones ip, correos, o cualquier dato de contacto
import enum


class TipoEvento(str, enum.Enum):
    """Los catorce eventos registrables. Declarados en orden de flujo."""

    # --- Origen: denunciante (sin identidad) ---
    DENUNCIA_RECIBIDA = "denuncia_recibida"
    EVIDENCIA_RECIBIDA = "evidencia_recibida"
    MENSAJE_AGREGADO = "mensaje_agregado"

    # --- Origen: sistema ---
    EVIDENCIA_SANEADA = "evidencia_saneada"
    EVIDENCIA_RECHAZADA = "evidencia_rechazada"

    # --- Origen: revisor (siempre con revisor_id) ---
    REVISOR_ASIGNADO = "revisor_asignado"
    GRAVEDAD_ASIGNADA = "gravedad_asignada"
    REVISION_EMITIDA = "revision_emitida"
    CASO_ESCALADO = "caso_escalado"
    CASO_DERIVADO = "caso_derivado"
    CASO_PUBLICADO = "caso_publicado"
    CASO_RECHAZADO = "caso_rechazado"
    EVIDENCIA_DESCARGADA = "evidencia_descargada"
    HILO_CERRADO_POR_REVISOR = "hilo_cerrado_por_revisor"


# CLAVES OBLIGATORIAS
PAYLOAD_MINIMO: dict[TipoEvento, tuple[str, ...]] = {
    TipoEvento.DENUNCIA_RECIBIDA: (
        "denuncia_id",
        "categoria_id",
        "institucion_id",
        "nivel_identidad",
    ),
    TipoEvento.EVIDENCIA_RECIBIDA: ("denuncia_id", "evidencia_id", "mime"),
    TipoEvento.MENSAJE_AGREGADO: ("denuncia_id", "mensaje_id", "autor"),
    TipoEvento.EVIDENCIA_SANEADA: ("evidencia_id", "sha256", "mime_final"),
    TipoEvento.EVIDENCIA_RECHAZADA: (
        "denuncia_id",
        "motivo",
        "mime_detectado",
    ),
    TipoEvento.REVISOR_ASIGNADO: ("denuncia_id", "revisor_id"),
    TipoEvento.GRAVEDAD_ASIGNADA: ("denuncia_id", "revisor_id", "gravedad"),
    TipoEvento.REVISION_EMITIDA: ("denuncia_id", "revisor_id", "decision"),
    TipoEvento.CASO_ESCALADO: ("denuncia_id", "revisor_id", "motivo"),
    TipoEvento.CASO_DERIVADO: (
        "denuncia_id",
        "revisor_id",
        "derivacion_id",
        "autoridad",
    ),
    TipoEvento.CASO_PUBLICADO: (
        "denuncia_id",
        "revisor_id",
        "publicacion_id",
    ),
    TipoEvento.CASO_RECHAZADO: ("denuncia_id", "revisor_id"),
    TipoEvento.EVIDENCIA_DESCARGADA: (
        "evidencia_id",
        "revisor_id",
        "marca_id",
        "sha256_copia",
    ),
    TipoEvento.HILO_CERRADO_POR_REVISOR: (
        "denuncia_id",
        "revisor_id",
        "motivo",
    ),
}

#claves prohibidas en cualquier payload 
CLAVES_PROHIBIDAS: frozenset[str] = frozenset(
    {
        "codigo",
        "codigo_hash",
        "codigo_seguimiento",
        "relato",
        "cuerpo",
        "ip",
        "direccion_ip",
        "correo",
        "email",
        "telefono",
        "nombre_archivo",
        "nombre_original",
        "user_agent",
    }
)


class PayloadInvalido(ValueError):
    """El payload no cumple el contrato del evento."""


def validar_payload(tipo: TipoEvento, payload: dict) -> None:
    """Comprueba que el payload tenga las claves minimas y ninguna prohibida.

    Se llama antes de encadenar. Una vez dentro de la bitacora un evento
    no se puede corregir: las reglas del motor lo impiden.
    """
    faltantes = set(PAYLOAD_MINIMO[tipo]) - set(payload)
    if faltantes:
        raise PayloadInvalido(
            f"{tipo.value}: faltan las claves {sorted(faltantes)}"
        )

    prohibidas = CLAVES_PROHIBIDAS & set(payload)
    if prohibidas:
        raise PayloadInvalido(
            f"{tipo.value}: claves prohibidas en un registro publico "
            f"{sorted(prohibidas)}"
        )