export type NivelIdentidad = "anonimo" | "seudonimo" | "publico";

const ETIQUETAS: Record<NivelIdentidad, string> = {
  anonimo: "anónimo total",
  seudonimo: "seudónimo",
  publico: "público voluntario",
};

/**
 * Barra persistente de estado de anonimato.
 *
 * Va en todos los pasos del asistente, no solo en el selector. GlobaLeaks
 * informa siempre del estado actual y aqui se hace igual: quien denuncia
 * debe poder saber en todo momento cuanto esta exponiendo.
 */
export function BarraAnonimato({
  nivel,
  onCambiar,
}: {
  nivel: NivelIdentidad;
  onCambiar: () => void;
}) {
  const esPublico = nivel === "publico";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "var(--sp-3)",
        flexWrap: "wrap",
        background: esPublico ? "var(--c-amber-05)" : "var(--c-navy-05)",
        borderBottom: `1px solid ${
          esPublico ? "var(--c-amber-70)" : "var(--c-navy-70)"
        }`,
        padding: "var(--sp-2) var(--sp-5)",
        fontSize: 14,
        color: esPublico ? "var(--c-amber-90)" : "var(--c-navy-90)",
      }}
    >
      <span>
        Nivel de identidad:{" "}
        <strong style={{ fontWeight: 500 }}>{ETIQUETAS[nivel]}</strong>
      </span>
      <button
        type="button"
        onClick={onCambiar}
        style={{
          background: "none",
          border: 0,
          color: "inherit",
          fontSize: 14,
          textDecoration: "underline",
          textUnderlineOffset: 2,
          cursor: "pointer",
          padding: "var(--sp-1) 0",
        }}
      >
        Cambiar
      </button>
    </div>
  );
}