import { useEffect, useState } from "react";
import { obtenerCatalogo } from "../api/cliente";
import { Aviso } from "../componentes/Aviso";
import { BarraAnonimato, type NivelIdentidad } from "../componentes/BarraAnonimato";
import { Boton } from "../componentes/Boton";
import { Progreso } from "../componentes/Progreso";
import { crearDenuncia } from "../api/cliente";
import { subirEvidencia } from "../api/cliente";
import { ErrorApi } from "../api/cliente";
import { SelectorIdentidad } from "./SelectorIdentidad";
export type BorradorDenuncia = {
  relato: string;
  categoriaId: number | null;
  institucionId: number | null;
  nivelIdentidad: NivelIdentidad;
  archivos: File[];
};


const VACIO: BorradorDenuncia = {
  relato: "",
  categoriaId: null,
  institucionId: null,
  nivelIdentidad: "anonimo",
  archivos: [],
};
type Catalogo = Awaited<ReturnType<typeof obtenerCatalogo>>;

const MINIMO_RELATO = 40;

const campo: React.CSSProperties = {
  width: "100%",
  padding: "var(--sp-2) var(--sp-3)",
  border: "1px solid var(--borde-input)",
  borderRadius: 2,
  background: "var(--superficie)",
};

const etiqueta: React.CSSProperties = {
  display: "block",
  fontWeight: 500,
  marginBottom: "var(--sp-1)",
};

const ayuda: React.CSSProperties = {
  fontSize: 14,
  color: "var(--texto-secundario)",
  margin: "var(--sp-1) 0 0",
};

export function Denunciar() {
  const [paso, setPaso] = useState(1);
  const [borrador, setBorrador] = useState<BorradorDenuncia>(VACIO);
  const [catalogo, setCatalogo] = useState<Catalogo | null>(null);
  const [errorCatalogo, setErrorCatalogo] = useState(false);
  const [resultado, setResultado] = useState<ResultadoEnvio | null>(null);
  useEffect(() => {
    obtenerCatalogo().then(setCatalogo).catch(() => setErrorCatalogo(true));
  }, []);
  function actualizar(cambios: Partial<BorradorDenuncia>) {
    setBorrador((previo) => ({ ...previo, ...cambios }));
  }
  if (paso === 0) {
    return (
      <SelectorIdentidad
        actual={borrador.nivelIdentidad}
        onElegir={(nivelIdentidad) => {
          actualizar({ nivelIdentidad });
          setPaso(1);
        }}
        onCancelar={() => setPaso(1)}
      />
    );
  }
  if (resultado) {
    return (
      <PantallaCodigo
        resultado={resultado}
        onSalir={() => {
          setResultado(null);
          setBorrador(VACIO);
          setPaso(1);
        }}
      />
    );
  }

  return (
    <>
      <BarraAnonimato
        nivel={borrador.nivelIdentidad}
        onCambiar={() => setPaso(0)}
      />


      <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
        <h1>Enviar denuncia</h1>
        <p style={{ color: "var(--texto-secundario)", marginBottom: "var(--sp-5)" }}>
          No se solicita ni se registra su nombre, correo ni dirección IP.
        </p>

        <Progreso pasoActual={paso} />

        {paso === 1 && (
          <PasoRelato
            valor={borrador.relato}
            onCambiar={(relato) => actualizar({ relato })}
            onSiguiente={() => setPaso(2)}
          />
        )}

        {paso === 2 && (
          <PasoClasificacion
            borrador={borrador}
            catalogo={catalogo}
            error={errorCatalogo}
            onCambiar={actualizar}
            onAtras={() => setPaso(1)}
            onSiguiente={() => setPaso(3)}
          />
        )}

        {paso === 3 && (
          <PasoEvidencia
            archivos={borrador.archivos}
            onCambiar={actualizar}
            onAtras={() => setPaso(2)}
            onSiguiente={() => setPaso(4)}
          />
        )}

        {paso === 4 && !resultado && (
          <PasoEnvio
            borrador={borrador}
            catalogo={catalogo}
            onAtras={() => setPaso(3)}
            onEnviado={setResultado}
          />
        )}
      </main>

    </>
  );
}

function PasoRelato({
  valor,
  onCambiar,
  onSiguiente,
}: {
  valor: string;
  onCambiar: (valor: string) => void;
  onSiguiente: () => void;
}) {
  const faltan = MINIMO_RELATO - valor.trim().length;

  return (
    <section>
      <h2>Qué ocurrió</h2>

      <Aviso nivel="informativo">
        Describa los hechos con el mayor detalle posible: fechas, montos,
        cargos involucrados. Evite incluir datos que lo identifiquen a usted.
      </Aviso>

      <label htmlFor="relato" style={etiqueta}>
        Relato de los hechos
      </label>
      <textarea
        id="relato"
        value={valor}
        onChange={(e) => onCambiar(e.target.value)}
        rows={8}
        aria-describedby="ayuda-relato"
        style={{ ...campo, resize: "vertical", lineHeight: 1.65 }}
      />
      <p id="ayuda-relato" style={ayuda}>
        {faltan > 0
          ? `Faltan ${faltan} caracteres para poder continuar.`
          : `${valor.trim().length} caracteres.`}
      </p>

      <div style={{ marginTop: "var(--sp-5)" }}>
        <Boton onClick={onSiguiente} disabled={faltan > 0}>
          Continuar a clasificación
        </Boton>
      </div>
    </section>
  );
}

function PasoClasificacion({
  borrador,
  catalogo,
  error,
  onCambiar,
  onAtras,
  onSiguiente,
}: {
  borrador: BorradorDenuncia;
  catalogo: Catalogo | null;
  error: boolean;
  onCambiar: (cambios: Partial<BorradorDenuncia>) => void;
  onAtras: () => void;
  onSiguiente: () => void;
}) {
  const completo =
    borrador.categoriaId !== null && borrador.institucionId !== null;

  if (error) {
    return (
      <Aviso nivel="critico" titulo="No se pudo cargar el catálogo">
        Revise su conexión y recargue la página. Su relato se conserva
        mientras no cierre esta pestaña.
      </Aviso>
    );
  }

  return (
    <section>
      <h2>Clasificación</h2>
      <p style={{ color: "var(--texto-secundario)" }}>
        Estos datos permiten dirigir el caso al revisor adecuado.
      </p>

      <div style={{ marginBottom: "var(--sp-4)" }}>
        <label htmlFor="categoria" style={etiqueta}>
          Tipo de acto denunciado
        </label>
        <select
          id="categoria"
          value={borrador.categoriaId ?? ""}
          disabled={!catalogo}
          onChange={(e) =>
            onCambiar({ categoriaId: Number(e.target.value) || null })
          }
          style={campo}
        >
          <option value="">
            {catalogo ? "Seleccione una categoría" : "Cargando…"}
          </option>
          {catalogo?.categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: "var(--sp-4)" }}>
        <label htmlFor="institucion" style={etiqueta}>
          Institución señalada
        </label>
        <select
          id="institucion"
          value={borrador.institucionId ?? ""}
          disabled={!catalogo}
          onChange={(e) =>
            onCambiar({ institucionId: Number(e.target.value) || null })
          }
          style={campo}
        >
          <option value="">
            {catalogo ? "Seleccione una institución" : "Cargando…"}
          </option>
          {catalogo?.instituciones.map((i) => (
            <option key={i.id} value={i.id}>
              {i.nombre}
            </option>
          ))}
        </select>
        <p style={ayuda}>
          Las instituciones de este portal son ficticias: el sistema se valida
          con datos sintéticos.
        </p>
      </div>

      <div style={{ display: "flex", gap: "var(--sp-3)", marginTop: "var(--sp-5)" }}>
        <Boton variante="secundario" onClick={onAtras}>
          Volver al relato
        </Boton>
        <Boton onClick={onSiguiente} disabled={!completo}>
          Continuar a evidencia
        </Boton>
      </div>
    </section>
  );
}

const FORMATOS_ACEPTADOS = "image/jpeg,image/png";
const LIMITE_MB = 15;

function PasoEvidencia({
  archivos,
  onCambiar,
  onAtras,
  onSiguiente,
}: {
  archivos: File[];
  onCambiar: (cambios: Partial<BorradorDenuncia>) => void;
  onAtras: () => void;
  onSiguiente: () => void;
}) {
  const [reconoce, setReconoce] = useState(false);
  const [rechazados, setRechazados] = useState<string[]>([]);

  function agregar(lista: FileList | null) {
    if (!lista) return;

    const validos: File[] = [];
    const malos: string[] = [];

    for (const archivo of Array.from(lista)) {
      if (archivo.size > LIMITE_MB * 1024 * 1024) {
        malos.push(`${archivo.name}: supera ${LIMITE_MB} MB`);
      } else {
        validos.push(archivo);
      }
    }

    setRechazados(malos);
    onCambiar({ archivos: [...archivos, ...validos] });
  }

  function quitar(indice: number) {
    onCambiar({ archivos: archivos.filter((_, i) => i !== indice) });
  }

  return (
    <section>
      <h2>Evidencia</h2>
      <p style={{ color: "var(--texto-secundario)" }}>
        Este paso es opcional. Puede enviar la denuncia sin adjuntos.
      </p>

      {/* Aviso bloqueante en dos parrafos separados. En uno solo, la gente
          lee la primera mitad y asume que esta cubierta. */}
      <Aviso nivel="advertencia" titulo="Antes de adjuntar un archivo">
        <p style={{ margin: "0 0 var(--sp-2)" }}>
          Lo que el archivo <strong style={{ fontWeight: 500 }}>guarda</strong>{" "}
          sobre usted se elimina: ubicación, fecha, marca y número de serie del
          equipo. El original se destruye y no se conserva copia.
        </p>
        <p style={{ margin: 0 }}>
          Lo que el archivo <strong style={{ fontWeight: 500 }}>muestra</strong>{" "}
          no se elimina. Si en la imagen aparece su escritorio, su firma, una
          matrícula o el reflejo de su rostro, revísela antes de continuar.
        </p>
      </Aviso>

      <label
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "var(--sp-2)",
          marginBottom: "var(--sp-4)",
          cursor: "pointer",
        }}
      >
        <input
          type="checkbox"
          checked={reconoce}
          onChange={(e) => setReconoce(e.target.checked)}
          style={{ marginTop: 5 }}
        />
        <span style={{ fontSize: 15 }}>
          He leído la advertencia y revisé el contenido visible de mis archivos.
        </span>
      </label>

      <div style={{ marginBottom: "var(--sp-4)" }}>
        <label htmlFor="archivos" style={etiqueta}>
          Archivos adjuntos
        </label>
        <input
          id="archivos"
          type="file"
          multiple
          accept={FORMATOS_ACEPTADOS}
          disabled={!reconoce}
          onChange={(e) => agregar(e.target.files)}
          style={{ ...campo, padding: "var(--sp-2)" }}
        />
        <p style={ayuda}>
          Se aceptan imágenes JPEG y PNG, hasta {LIMITE_MB} MB cada una.
        </p>
      </div>

      {rechazados.length > 0 && (
        <Aviso nivel="critico" titulo="Archivos no aceptados">
          <ul style={{ margin: 0, paddingLeft: "var(--sp-4)" }}>
            {rechazados.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </Aviso>
      )}

      {archivos.length > 0 && (
        <table style={{ width: "100%", marginBottom: "var(--sp-4)" }}>
          <caption
            style={{
              textAlign: "left",
              fontSize: 14,
              color: "var(--texto-secundario)",
              paddingBottom: "var(--sp-2)",
            }}
          >
            {archivos.length} archivo{archivos.length > 1 ? "s" : ""} por enviar
          </caption>
          <tbody>
            {archivos.map((archivo, indice) => (
              <tr
                key={`${archivo.name}-${indice}`}
                style={{ borderBottom: "1px solid var(--c-gray-20)" }}
              >
                <td style={{ padding: "var(--sp-2) 0", fontSize: 15 }}>
                  {archivo.name}
                </td>
                <td
                  style={{
                    padding: "var(--sp-2) 0",
                    fontSize: 14,
                    color: "var(--texto-secundario)",
                    fontFamily: "var(--mono)",
                    textAlign: "right",
                  }}
                >
                  {(archivo.size / 1024).toFixed(0)} KB
                </td>
                <td style={{ padding: "var(--sp-2) 0", textAlign: "right" }}>
                  <Boton variante="texto" onClick={() => quitar(indice)}>
                    Quitar
                  </Boton>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ display: "flex", gap: "var(--sp-3)", marginTop: "var(--sp-5)" }}>
        <Boton variante="secundario" onClick={onAtras}>
          Volver a clasificación
        </Boton>
        <Boton onClick={onSiguiente}>Continuar a envío</Boton>
      </div>
    </section>
  );
}

type ResultadoEnvio = {
  denunciaId: number;
  codigo: string;
  adjuntosFallidos: string[];
};

function PasoEnvio({
  borrador,
  catalogo,
  onAtras,
  onEnviado,
}: {
  borrador: BorradorDenuncia;
  catalogo: Catalogo | null;
  onAtras: () => void;
  onEnviado: (resultado: ResultadoEnvio) => void;
}) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const categoria = catalogo?.categorias.find(
    (c) => c.id === borrador.categoriaId,
  );
  const institucion = catalogo?.instituciones.find(
    (i) => i.id === borrador.institucionId,
  );

  async function enviar() {
    setEnviando(true);
    setError(null);

    try {
      const denuncia = await crearDenuncia({
        categoria_id: borrador.categoriaId!,
        institucion_id: borrador.institucionId!,
        nivel_identidad: borrador.nivelIdentidad,
        relato: borrador.relato,
      });

      // Los adjuntos van despues, ya con el codigo emitido. Si alguno
      // falla, la denuncia sigue siendo valida: se informa cual no entro
      // en vez de perder todo el envio.
      const fallidos: string[] = [];
      for (const archivo of borrador.archivos) {
        try {
          await subirEvidencia(denuncia.denuncia_id, denuncia.codigo, archivo);
        } catch (e) {
          fallidos.push(
            `${archivo.name}: ${e instanceof ErrorApi ? e.message : "no se pudo adjuntar"}`,
          );
        }
      }

      onEnviado({
        denunciaId: denuncia.denuncia_id,
        codigo: denuncia.codigo,
        adjuntosFallidos: fallidos,
      });
    } catch (e) {
      setError(
        e instanceof ErrorApi
          ? e.message
          : "No se pudo enviar la denuncia. Revise su conexión e inténtelo de nuevo.",
      );
      setEnviando(false);
    }
  }

  return (
    <section>
      <h2>Revisar y enviar</h2>

      {error && (
        <Aviso nivel="critico" titulo="El envío no se completó">
          {error}
        </Aviso>
      )}

      <dl style={{ margin: "0 0 var(--sp-5)" }}>
        <Resumen etiqueta="Tipo de acto" valor={categoria?.nombre ?? "—"} />
        <Resumen etiqueta="Institución" valor={institucion?.nombre ?? "—"} />
        <Resumen
          etiqueta="Nivel de identidad"
          valor={
            borrador.nivelIdentidad === "anonimo"
              ? "anónimo total"
              : borrador.nivelIdentidad === "seudonimo"
                ? "seudónimo"
                : "público voluntario"
          }
        />
        <Resumen
          etiqueta="Adjuntos"
          valor={
            borrador.archivos.length === 0
              ? "ninguno"
              : `${borrador.archivos.length} archivo${borrador.archivos.length > 1 ? "s" : ""}`
          }
        />
      </dl>

      <div style={{ marginBottom: "var(--sp-5)" }}>
        <p style={{ ...etiqueta, marginBottom: "var(--sp-2)" }}>Relato</p>
        <div
          style={{
            border: "1px solid var(--borde)",
            padding: "var(--sp-3)",
            fontSize: 15,
            lineHeight: 1.65,
            whiteSpace: "pre-wrap",
            maxHeight: 200,
            overflowY: "auto",
          }}
        >
          {borrador.relato}
        </div>
      </div>

      <Aviso nivel="informativo">
        Al enviar recibirá un código de seguimiento. Se muestra una sola vez y
        no puede recuperarse: es la única forma de consultar su caso.
      </Aviso>

      <div style={{ display: "flex", gap: "var(--sp-3)", marginTop: "var(--sp-5)" }}>
        <Boton variante="secundario" onClick={onAtras} disabled={enviando}>
          Volver a evidencia
        </Boton>
        <Boton onClick={enviar} disabled={enviando}>
          {enviando ? "Enviando…" : "Enviar denuncia"}
        </Boton>
      </div>
    </section>
  );
}

function Resumen({ etiqueta: texto, valor }: { etiqueta: string; valor: string }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "var(--sp-3)",
        padding: "var(--sp-2) 0",
        borderBottom: "1px solid var(--c-gray-20)",
      }}
    >
      <dt style={{ width: 180, color: "var(--texto-secundario)", fontSize: 15 }}>
        {texto}
      </dt>
      <dd style={{ margin: 0, fontSize: 15 }}>{valor}</dd>
    </div>
  );
}

function PantallaCodigo({
  resultado,
  onSalir,
}: {
  resultado: ResultadoEnvio;
  onSalir: () => void;
}) {
  const [copiado, setCopiado] = useState(false);
  const [descargado, setDescargado] = useState(false);
  const [confirmaGuardado, setConfirmaGuardado] = useState(false);

  async function copiar() {
    await navigator.clipboard.writeText(resultado.codigo);
    setCopiado(true); // Persistente: no se desvanece a los tres segundos.
  }

  function descargar() {
    const texto = [
      "Portal Nacional de Denuncias de Corrupcion",
      "",
      `Codigo de seguimiento: ${resultado.codigo}`,
      `Caso numero: ${resultado.denunciaId}`,
      "",
      "Con este codigo puede consultar el estado de su caso y responder",
      "al revisor. No existe forma de recuperarlo: el portal solo guarda",
      "su huella criptografica, no el codigo.",
      "",
      "Guarde este archivo en un lugar seguro.",
    ].join("\n");

    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(
      new Blob([texto], { type: "text/plain;charset=utf-8" }),
    );
    enlace.download = "codigo-seguimiento-pndc.txt";
    enlace.click();
    URL.revokeObjectURL(enlace.href);
    setDescargado(true);
  }

  return (
    <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
      <h1>Denuncia recibida</h1>

      <Aviso nivel="critico" titulo="Guarde este código ahora">
        <p style={{ margin: "0 0 var(--sp-2)" }}>
          Es la única forma de consultar su caso y de responder al revisor.
        </p>
        <p style={{ margin: 0 }}>
          No puede recuperarse. Nadie en el portal puede reconstruirlo, porque
          solo se guarda su huella criptográfica y no el código.
        </p>
      </Aviso>

      <div
        style={{
          border: "1px solid var(--borde-input)",
          background: "var(--superficie-alt)",
          padding: "var(--sp-5)",
          textAlign: "center",
          marginBottom: "var(--sp-4)",
        }}
      >
        <p
          style={{
            fontFamily: "var(--mono)",
            fontSize: 28,
            fontWeight: 500,
            letterSpacing: "0.05em",
            margin: 0,
            wordBreak: "break-all",
          }}
        >
          {resultado.codigo}
        </p>
      </div>

      <div
        style={{
          display: "flex",
          gap: "var(--sp-3)",
          flexWrap: "wrap",
          marginBottom: "var(--sp-4)",
        }}
      >
        <Boton onClick={copiar}>
          {copiado ? "Copiado al portapapeles" : "Copiar código"}
        </Boton>
        <Boton variante="secundario" onClick={descargar}>
          {descargado ? "Archivo descargado" : "Descargar como archivo"}
        </Boton>
      </div>

      {resultado.adjuntosFallidos.length > 0 && (
        <Aviso nivel="advertencia" titulo="Algunos archivos no se adjuntaron">
          <p style={{ margin: "0 0 var(--sp-2)" }}>
            La denuncia se registró correctamente. Puede volver más tarde con su
            código para adjuntarlos.
          </p>
          <ul style={{ margin: 0, paddingLeft: "var(--sp-4)" }}>
            {resultado.adjuntosFallidos.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </Aviso>
      )}

      <label
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "var(--sp-2)",
          padding: "var(--sp-3) 0",
          borderTop: "1px solid var(--borde)",
          cursor: "pointer",
        }}
      >
        <input
          type="checkbox"
          checked={confirmaGuardado}
          onChange={(e) => setConfirmaGuardado(e.target.checked)}
          style={{ marginTop: 5 }}
        />
        <span style={{ fontSize: 15 }}>
          Confirmo que guardé el código en un lugar seguro.
        </span>
      </label>

      <Boton onClick={onSalir} disabled={!confirmaGuardado}>
        Terminar
      </Boton>
    </main>
  );
}