import { useEffect, useState } from "react";

import { obtenerCasosPublicados, obtenerRanking } from "../api/cliente";
import { Aviso } from "../componentes/Aviso";

type Ranking = Awaited<ReturnType<typeof obtenerRanking>>;
type Casos = Awaited<ReturnType<typeof obtenerCasosPublicados>>;

const TOPE_RANKING = 10;
const LIMITE_TEXTO = 320;

export function Publico() {
  const [ranking, setRanking] = useState<Ranking | null>(null);
  const [casos, setCasos] = useState<Casos | null>(null);
  const [verTodas, setVerTodas] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([obtenerRanking(), obtenerCasosPublicados()])
      .then(([r, c]) => {
        setRanking(r);
        setCasos(c);
      })
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
        <Aviso nivel="critico" titulo="No se pudieron cargar los datos">
          Revise su conexión y recargue la página.
        </Aviso>
      </main>
    );
  }

  const restantes = ranking
    ? ranking.instituciones.length - TOPE_RANKING
    : 0;

  return (
    <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
      <h1>Denuncias recibidas por institución</h1>

      {/* La aclaracion va ANTES de la tabla, no debajo: un conteo de
          denuncias no es una medida de corrupcion, y quien lea la tabla
          debe saberlo antes de interpretarla. */}
      <Aviso nivel="advertencia" titulo="Cómo leer este conteo">
        {ranking?.aclaracion ??
          "Las denuncias de este portal no están verificadas judicialmente."}
      </Aviso>

      {!ranking ? (
        <p style={{ color: "var(--texto-secundario)" }}>Cargando…</p>
      ) : ranking.instituciones.length === 0 ? (
        <p style={{ color: "var(--texto-secundario)" }}>
          Todavía no hay casos publicados.
        </p>
      ) : (
        <>
          <table style={{ width: "100%", marginBottom: "var(--sp-3)" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid var(--c-navy-70)" }}>
                <th style={celdaEncabezado}>Institución</th>
                <th style={celdaEncabezado}>Tipo</th>
                <th style={{ ...celdaEncabezado, textAlign: "right" }}>
                  Casos
                </th>
              </tr>
            </thead>
            <tbody>
              {(verTodas
                ? ranking.instituciones
                : ranking.instituciones.slice(0, TOPE_RANKING)
              ).map((i) => (
                <tr
                  key={i.nombre}
                  style={{ borderBottom: "1px solid var(--c-gray-20)" }}
                >
                  <td style={celda}>{i.nombre}</td>
                  <td
                    style={{
                      ...celda,
                      color: "var(--texto-secundario)",
                      fontSize: 14,
                    }}
                  >
                    {i.tipo.replace(/_/g, " ")}
                  </td>
                  <td
                    style={{
                      ...celda,
                      textAlign: "right",
                      fontFamily: "var(--mono)",
                    }}
                  >
                    {i.casos}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {restantes > 0 && !verTodas && (
            <button
              type="button"
              onClick={() => setVerTodas(true)}
              style={enlace}
            >
              Ver las {restantes} instituciones restantes
            </button>
          )}

          <div style={{ marginBottom: "var(--sp-6)" }} />
        </>
      )}

      {ranking && ranking.categorias.length > 0 && (
        <>
          <h2>Por tipo de acto</h2>
          <table style={{ width: "100%", marginBottom: "var(--sp-6)" }}>
            <tbody>
              {ranking.categorias.map((c) => (
                <tr
                  key={c.nombre}
                  style={{ borderBottom: "1px solid var(--c-gray-20)" }}
                >
                  <td style={celda}>{c.nombre}</td>
                  <td
                    style={{
                      ...celda,
                      textAlign: "right",
                      fontFamily: "var(--mono)",
                    }}
                  >
                    {c.casos}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h2>
        Casos publicados
        {casos && casos.length > 0 && (
          <span
            style={{
              fontSize: 15,
              fontWeight: 400,
              color: "var(--texto-secundario)",
              marginLeft: "var(--sp-2)",
            }}
          >
            {casos.length}
          </span>
        )}
      </h2>
      <p
        style={{
          color: "var(--texto-secundario)",
          marginBottom: "var(--sp-4)",
        }}
      >
        Lo que sigue no es el relato original de quien denunció: es una
        versión redactada por un revisor, de la que se eliminó todo lo que
        identificaría a terceros no verificados.
      </p>

      {!casos ? (
        <p style={{ color: "var(--texto-secundario)" }}>Cargando…</p>
      ) : casos.length === 0 ? (
        <p style={{ color: "var(--texto-secundario)" }}>
          Ningún caso ha sido publicado todavía.
        </p>
      ) : (
        casos.map((caso) => <CasoPublicado key={caso.caso_id} caso={caso} />)
      )}
    </main>
  );
}

function CasoPublicado({ caso }: { caso: Casos[number] }) {
  const [expandido, setExpandido] = useState(false);
  const largo = caso.texto.length > LIMITE_TEXTO;

  const texto =
    expandido || !largo
      ? caso.texto
      : `${caso.texto.slice(0, LIMITE_TEXTO).trimEnd()}…`;

  return (
    <article
      style={{
        border: "1px solid var(--borde)",
        padding: "var(--sp-4)",
        marginBottom: "var(--sp-4)",
      }}
    >
      <h3 style={{ marginBottom: "var(--sp-1)" }}>{caso.categoria}</h3>
      <p
        style={{
          fontSize: 14,
          color: "var(--texto-secundario)",
          margin: "0 0 var(--sp-3)",
        }}
      >
        {caso.institucion}
        {" · "}
        caso {caso.caso_id}
        {caso.gravedad && ` · gravedad ${caso.gravedad}`}
      </p>
      <p style={{ margin: 0, fontSize: 15, lineHeight: 1.65 }}>{texto}</p>

      {largo && (
        <button
          type="button"
          onClick={() => setExpandido(!expandido)}
          style={{ ...enlace, paddingTop: "var(--sp-2)" }}
        >
          {expandido ? "Mostrar menos" : "Leer el caso completo"}
        </button>
      )}
    </article>
  );
}

const celdaEncabezado: React.CSSProperties = {
  textAlign: "left",
  padding: "var(--sp-2) 0",
  fontWeight: 500,
  fontSize: 14,
};

const celda: React.CSSProperties = {
  padding: "var(--sp-2) 0",
  fontSize: 15,
};

const enlace: React.CSSProperties = {
  background: "none",
  border: 0,
  color: "var(--enlace)",
  fontSize: 15,
  textDecoration: "underline",
  textUnderlineOffset: 2,
  cursor: "pointer",
  padding: 0,
};