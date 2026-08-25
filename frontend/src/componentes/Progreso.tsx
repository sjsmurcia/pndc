const PASOS = ["Relato", "Clasificación", "Evidencia", "Envío"] as const;

/**
 * Indicador de progreso del asistente.
 *
 * Borde superior de 3px: navy-70 para completados, gray-10 para
 * pendientes. El paso actual va en gray-90 y peso 500, para que se
 * distinga sin depender solo del color.
 */
export function Progreso({ pasoActual }: { pasoActual: number }) {
  return (
    <ol
      aria-label="Progreso del asistente"
      style={{
        display: "flex",
        listStyle: "none",
        margin: "0 0 var(--sp-5)",
        padding: 0,
        gap: "var(--sp-1)",
      }}
    >
      {PASOS.map((nombre, indice) => {
        const numero = indice + 1;
        const completado = numero < pasoActual;
        const actual = numero === pasoActual;

        return (
          <li
            key={nombre}
            aria-current={actual ? "step" : undefined}
            style={{
              flex: 1,
              borderTop: `3px solid ${
                completado || actual ? "var(--c-navy-70)" : "var(--c-gray-10)"
              }`,
              paddingTop: "var(--sp-2)",
              fontSize: 14,
              fontWeight: actual ? 500 : 400,
              color: actual ? "var(--c-gray-90)" : "var(--texto-secundario)",
            }}
          >
            <span style={{ fontFamily: "var(--mono)", fontSize: 13 }}>
              {numero}
            </span>{" "}
            {nombre}
          </li>
        );
      })}
    </ol>
  );
}