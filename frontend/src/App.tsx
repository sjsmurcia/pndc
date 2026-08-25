import { Denunciar } from "./paginas/Denunciar";

export default function App() {
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
        </header>

        <Denunciar />
      </div>
    </div>
  );
}