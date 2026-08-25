import type { ReactNode } from "react";

export type NivelAviso = "informativo" | "advertencia" | "critico" | "confirmacion";

const ESTILOS: Record<NivelAviso, { fondo: string; borde: string; texto: string }> = {
  informativo: { fondo: "var(--c-navy-05)", borde: "var(--c-navy-70)", texto: "var(--c-navy-90)" },
  advertencia: { fondo: "var(--c-amber-05)", borde: "var(--c-amber-70)", texto: "var(--c-amber-90)" },
  critico: { fondo: "var(--c-red-05)", borde: "var(--c-red-70)", texto: "var(--c-red-90)" },
  confirmacion: { fondo: "var(--c-green-05)", borde: "var(--c-green-70)", texto: "var(--c-green-90)" },
};

/**
 * Aviso segun los cuatro niveles del manual.
 *
 * Sin sombra, sin esquinas redondeadas, sin boton de cerrar. Los avisos
 * criticos no se descartan: si el usuario puede quitarlos de en medio,
 * dejan de cumplir su funcion.
 */
export function Aviso({
  nivel,
  titulo,
  children,
}: {
  nivel: NivelAviso;
  titulo?: string;
  children: ReactNode;
}) {
  const e = ESTILOS[nivel];
  return (
    <div
      role={nivel === "critico" ? "alert" : "note"}
      style={{
        background: e.fondo,
        border: `1px solid ${e.borde}`,
        borderLeft: `6px solid ${e.borde}`,
        borderRadius: 0,
        color: e.texto,
        padding: "var(--sp-3) var(--sp-4)",
        marginBottom: "var(--sp-4)",
      }}
    >
      {titulo && (
        <p style={{ fontWeight: 500, margin: "0 0 var(--sp-1)" }}>{titulo}</p>
      )}
      <div style={{ fontSize: 15, lineHeight: 1.6 }}>{children}</div>
    </div>
  );
}