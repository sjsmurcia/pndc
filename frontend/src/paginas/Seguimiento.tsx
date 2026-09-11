import { useState } from "react";

import { consultarCaso, escribirMensaje, ErrorApi } from "../api/cliente";
import { Aviso } from "../componentes/Aviso";
import { Boton } from "../componentes/Boton";

type Caso = Awaited<ReturnType<typeof consultarCaso>>;

const ESTADOS: Record<string, { texto: string; explicacion: string }> = {
  recibida: {
    texto: "Recibida",
    explicacion: "Su denuncia entró al sistema y espera revisión.",
  },
  en_saneamiento: {
    texto: "Procesando adjuntos",
    explicacion: "Los archivos que envió se están limpiando de metadatos.",
  },
  en_triaje: {
    texto: "En revisión",
    explicacion: "Un revisor identificado está evaluando el caso.",
  },
  en_revision_doble: {
    texto: "En revisión por dos personas",
    explicacion:
      "El caso se clasificó como grave, así que requiere que dos revisores coincidan.",
  },
  escalada: {
    texto: "Escalada",
    explicacion:
      "Los revisores no coincidieron y el caso pasó a un supervisor.",
  },
  en_redaccion: {
    texto: "En redacción",
    explicacion:
      "El caso procede. Se está preparando la versión que se publicará.",
  },
  critica: {
    texto: "Clasificada como crítica",
    explicacion:
      "Por su gravedad, el caso no se publicará y será derivado a la autoridad.",
  },
  derivada: {
    texto: "Derivada a la autoridad",
    explicacion: "El caso salió del portal y está en manos de la autoridad.",
  },
  publicada: {
    texto: "Publicada",
    explicacion: "Una versión redactada del caso ya es pública.",
  },
  rechazada: {
    texto: "Rechazada",
    explicacion:
      "Tras la revisión se determinó que el caso no procede. La decisión queda registrada.",
  },
};

const campo: React.CSSProperties = {
  width: "100%",
  padding: "var(--sp-2) var(--sp-3)",
  border: "1px solid var(--borde-input)",
  borderRadius: 2,
  background: "var(--superficie)",
};

export function Seguimiento() {
  const [codigo, setCodigo] = useState("");
  const [caso, setCaso] = useState<Caso | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [buscando, setBuscando] = useState(false);

  async function buscar() {
    setBuscando(true);
    setError(null);
    try {
      setCaso(await consultarCaso(codigo));
    } catch (e) {
      setCaso(null);
      setError(
        e instanceof ErrorApi
          ? e.message
          : "No se pudo consultar el caso. Revise su conexión.",
      );
    }
    setBuscando(false);
  }

  if (caso) {
    return (
      <DetalleCaso
        caso={caso}
        codigo={codigo}
        onActualizar={setCaso}
        onSalir={() => {
          setCaso(null);
          setCodigo("");
        }}
      />
    );
  }

  return (
    <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
      <h1>Seguimiento de una denuncia</h1>
      <p style={{ color: "var(--texto-secundario)", marginBottom: "var(--sp-5)" }}>
        Escriba el código que recibió al enviar su denuncia. No hace falta
        cuenta ni contraseña.
      </p>

      {error && (
        <Aviso nivel="critico" titulo="No se encontró el caso">
          {error}
        </Aviso>
      )}

      <label htmlFor="codigo" style={{ display: "block", fontWeight: 500, marginBottom: "var(--sp-1)" }}>
        Código de seguimiento
      </label>
      <input
        id="codigo"
        value={codigo}
        onChange={(e) => setCodigo(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && codigo && buscar()}
        placeholder="PNDC-XXXX-XXXX-XXXX"
        aria-describedby="ayuda-codigo"
        style={{
          ...campo,
          fontFamily: "var(--mono)",
          fontSize: 18,
          letterSpacing: "0.05em",
          maxWidth: 420,
        }}
      />
      <p
        id="ayuda-codigo"
        style={{ fontSize: 14, color: "var(--texto-secundario)", margin: "var(--sp-1) 0 var(--sp-4)" }}
      >
        Puede escribirlo con o sin guiones, en mayúsculas o minúsculas.
      </p>

      <div style={{
        marginBottom:"var(--sp-5)"}}>
    

      <Boton onClick={buscar} disabled={!codigo.trim() || buscando}>
        {buscando ? "Consultando…" : "Consultar caso"}
      </Boton>
</div>
      <Aviso nivel="informativo" titulo="Si perdió su código">
        No hay forma de recuperarlo. Su
        denuncia sigue su curso igualmente, pero ya no podrá consultarla ni
        responder al revisor.
      </Aviso>
    </main>
  );
}

function DetalleCaso({
  caso,
  codigo,
  onActualizar,
  onSalir,
}: {
  caso: Caso;
  codigo: string;
  onActualizar: (caso: Caso) => void;
  onSalir: () => void;
}) {
  const [mensaje, setMensaje] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const estado = ESTADOS[caso.estado] ?? {
    texto: caso.estado,
    explicacion: "",
  };

  const cerrado = ["publicada", "rechazada", "derivada"].includes(caso.estado);

  async function enviar() {
    setEnviando(true);
    setError(null);
    try {
      await escribirMensaje(codigo, mensaje);
      onActualizar(await consultarCaso(codigo));
      setMensaje("");
    } catch (e) {
      setError(
        e instanceof ErrorApi ? e.message : "No se pudo enviar el mensaje.",
      );
    }
    setEnviando(false);
  }

  return (
    <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
      <h1>Caso {caso.denuncia_id}</h1>

      <div
        style={{
          border: "1px solid var(--borde)",
          borderLeft: "6px solid var(--c-navy-70)",
          background: "var(--c-navy-05)",
          padding: "var(--sp-3) var(--sp-4)",
          marginBottom: "var(--sp-5)",
        }}
      >
        <p style={{ fontWeight: 500, margin: "0 0 var(--sp-1)", color: "var(--c-navy-90)" }}>
          {estado.texto}
        </p>
        <p style={{ margin: 0, fontSize: 15, color: "var(--c-navy-90)" }}>
          {estado.explicacion}
        </p>
      </div>

      <dl style={{ margin: "0 0 var(--sp-5)" }}>
        <Dato etiqueta="Tipo de acto" valor={caso.categoria} />
        <Dato etiqueta="Institución" valor={caso.institucion} />
        <Dato
          etiqueta="Gravedad"
          valor={caso.gravedad ?? "aún sin clasificar"}
        />
      </dl>

      <h2>Su relato</h2>
      <div
        style={{
          border: "1px solid var(--borde)",
          padding: "var(--sp-3)",
          fontSize: 15,
          lineHeight: 1.65,
          whiteSpace: "pre-wrap",
          marginBottom: "var(--sp-5)",
        }}
      >
        {caso.relato}
      </div>

      <h2>Mensajes</h2>

      {caso.mensajes.length === 0 ? (
        <p style={{ color: "var(--texto-secundario)" }}>
          Todavía no hay mensajes. Si un revisor necesita más información,
          escribirá aquí y lo verá la próxima vez que consulte su caso.
        </p>
      ) : (
        <div style={{ marginBottom: "var(--sp-4)" }}>
          {caso.mensajes.map((m) => {
            const esRevisor = m.autor === "revisor";
            return (
              <div
                key={m.id}
                style={{
                  border: "1px solid var(--borde)",
                  borderLeft: `6px solid ${
                    esRevisor ? "var(--c-navy-70)" : "var(--c-gray-40)"
                  }`,
                  background: esRevisor ? "var(--c-navy-05)" : "var(--superficie-alt)",
                  padding: "var(--sp-3)",
                  marginBottom: "var(--sp-3)",
                }}
              >
                <p
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: "var(--texto-secundario)",
                    margin: "0 0 var(--sp-1)",
                  }}
                >
                  {esRevisor ? "Revisor" : "Usted"}
                  {" · "}
                  <span style={{ fontWeight: 400 }}>
                    {new Date(m.creado_en).toLocaleString("es")}
                  </span>
                </p>
                <p style={{ margin: 0, fontSize: 15, whiteSpace: "pre-wrap" }}>
                  {m.cuerpo}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {error && (
        <Aviso nivel="critico" titulo="No se pudo enviar">
          {error}
        </Aviso>
      )}

      {cerrado ? (
        <Aviso nivel="informativo">
          Este caso ya está cerrado y no admite mensajes nuevos.
        </Aviso>
      ) : (
        <>
          <label
            htmlFor="mensaje"
            style={{ display: "block", fontWeight: 500, marginBottom: "var(--sp-1)" }}
          >
            Ampliar la denuncia o responder al revisor
          </label>
          <textarea
            id="mensaje"
            value={mensaje}
            onChange={(e) => setMensaje(e.target.value)}
            rows={5}
            style={{ ...campo, resize: "vertical", lineHeight: 1.65 }}
          />
          <div style={{ marginTop: "var(--sp-3)" }}>
            <Boton
              onClick={enviar}
              disabled={mensaje.trim().length < 5 || enviando}
            >
              {enviando ? "Enviando…" : "Enviar mensaje"}
            </Boton>
          </div>
        </>
      )}

      <div style={{ marginTop: "var(--sp-6)" }}>
        <Boton variante="texto" onClick={onSalir}>
          Consultar otro caso
        </Boton>
      </div>
    </main>
  );
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "var(--sp-3)",
        padding: "var(--sp-2) 0",
        borderBottom: "1px solid var(--c-gray-20)",
      }}
    >
      <dt style={{ width: 160, color: "var(--texto-secundario)", fontSize: 15 }}>
        {etiqueta}
      </dt>
      <dd style={{ margin: 0, fontSize: 15 }}>{valor}</dd>
    </div>
  );
}