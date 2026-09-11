import { useState } from "react";
import { Denunciar } from "./paginas/Denunciar";
import { Verificar } from "./paginas/Verificar";
import { Seguimiento } from "./paginas/Seguimiento";
type Vista = "denunciar" | "seguimiento" | "verificar";
export default function App() {
  const [vista, setVista] = useState<Vista>("denunciar");
  return (
    <div style={{ minHeight: "100vh", background: "var(--superficie-alt)" }}>
      <div
        style={{
          maxWidth: 900,
          margin: "0 auto",
          background: "var(--superficie)",
          borderLeft: "1px solid var(--c-gray-10)",
          borderRight: "1px solid var(--c-gray-10)",
          minHeight: "100vh",
        }}
      >
        <header style={{ borderBottom: "1px solid var(--borde)" }}>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: "var(--sp-2)",
              padding: "var(--sp-3) var(--sp-5)",
            }}
          >
            <span
              style={{
                fontSize: 19,
                fontWeight: 500,
                color: "var(--c-navy-70)",
                letterSpacing: "-0.01em",
              }}
            >
              PNDC
            </span>
            <span style={{ fontSize: 14, color: "var(--texto-secundario)" }}>
              Portal Nacional de Denuncias de Corrupción
            </span>
          </div>
          <nav style={{
            display: "flex",
            gap: "var(--sp-5)",
            padding: "0 var(--sp-5) var(--sp-2)"
          }}>
            <button
              type="button"
              onClick={() => setVista("denunciar")}
              style={enlaceNav(vista === "denunciar")}
            >
              Denunciar
            </button>
            <button
              type="button"
              onClick={() => setVista("verificar")}
              style={enlaceNav(vista === "verificar")}
            >
              Verificar registro
            </button>
            <button
              type="button"
              onClick={() => setVista("seguimiento")}
              style={enlaceNav(vista === "seguimiento")}
            >
              Seguimiento
            </button>
          </nav>
        </header>

        {vista === "denunciar" && <Denunciar />}
        {vista === "seguimiento" && <Seguimiento />}
        {vista === "verificar" && <Verificar />}
        <footer
          style={{
            borderTop: "1px solid var(--borde)",
            padding: "var(--sp-5)",
          }}
        >
          <p
            style={{
              fontSize: 13,
              color: "var(--texto-secundario)",
              margin: 0,
            }}
          >
          </p>
          <p
            style={{
              fontSize: 13,
              color: "var(--texto-secundario)",
              margin: "var(--sp-2) 0 0",
            }}
          >
            Desarrollado por Jessel Murcia.
          </p>
        </footer>
      </div>
    </div>
  );
}
function enlaceNav(activo: boolean): React.CSSProperties {
  return {
    background: "none",
    border: 0,
    padding: "var(--sp-1) 0",
    fontSize: 15,
    fontWeight: activo ? 500 : 400,
    color: activo ? "var(--c-navy-70)" : "var(--texto-secundario)",
    borderBottom: activo ? "2px solid var(--c-navy-70)" : "2px solid transparent",
    cursor: "pointer",
  };
}