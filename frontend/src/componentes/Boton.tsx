import type { ButtonHTMLAttributes } from "react";

type Variante = "primario" | "secundario" | "texto";

const BASE = {
  fontSize: 15,
  fontWeight: 500,
  padding: "10px var(--sp-4)",
  borderRadius: 2,
  cursor: "pointer",
} as const;

const VARIANTES: Record<Variante, React.CSSProperties> = {
  primario: {
    ...BASE,
    background: "var(--accion)",
    color: "#fff",
    border: 0,
  },
  secundario: {
    ...BASE,
    background: "var(--superficie)",
    color: "var(--texto)",
    border: "1px solid var(--borde-input)",
  },
  texto: {
    ...BASE,
    background: "none",
    color: "var(--enlace)",
    border: 0,
    padding: "10px 0",
    textDecoration: "underline",
    textUnderlineOffset: 2,
  },
};

export function Boton({
  variante = "primario",
  style,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante }) {
  return (
    <button
      {...props}
      style={{
        ...VARIANTES[variante],
        ...(props.disabled ? { opacity: 0.5, cursor: "not-allowed" } : {}),
        ...style,
      }}
    />
  );
}