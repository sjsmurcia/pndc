import { EstadoCadena } from "../componentes/EstadoCadena";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8001";

/**
 * Pagina publica de verificacion.
 *
 * Aqui vive el indicador de integridad, no en el pie del formulario:
 * quien llega a denunciar no deberia encontrarse un aviso tecnico antes
 * de escribir. Quien quiere auditar, viene a esta pagina.
 */
export function Verificar() {
  return (
    <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
      <h1>Verificar el registro</h1>
      <p style={{ color: "var(--texto-secundario)", marginBottom: "var(--sp-5)" }}>
        Cada acción de los revisores queda anotada en un registro encadenado
        por huellas criptográficas. Alterar o borrar una anotación rompe la
        cadena, y la ruptura es detectable por cualquiera.
      </p>

      <EstadoCadena />

      <h2 style={{ marginTop: "var(--sp-6)" }}>Verificarlo usted mismo</h2>
      <p>
        La comprobación de arriba la hace el propio portal, así que no prueba
        gran cosa: un sistema que se declara íntegro a sí mismo no es una
        garantía. Lo que sigue sí lo es.
      </p>

      <ol style={{ paddingLeft: "var(--sp-4)" }}>
        <li style={{ marginBottom: "var(--sp-3)" }}>
          Descargue el registro completo en formato JSON:{" "}
          <a href={`${BASE}/api/v1/publico/bitacora?limite=5000`}>
            bitácora completa
          </a>
        </li>
        <li style={{ marginBottom: "var(--sp-3)" }}>
          Obtenga el verificador desde el repositorio del proyecto. Es un
          programa independiente del portal: se conecta con un rol que solo
          puede leer y recalcula la cadena desde cero.
        </li>
        <li style={{ marginBottom: "var(--sp-3)" }}>
          Ejecútelo. Si algún registro fue alterado, le indicará el número
          exacto del evento donde la cadena deja de cuadrar.
        </li>
      </ol>

      <h2 style={{ marginTop: "var(--sp-6)" }}>Qué contiene el registro</h2>
      <p>
        Identificadores de casos, decisiones de los revisores y marcas de
        tiempo. Nunca el relato de una denuncia, el contenido de un mensaje,
        el código de seguimiento ni dato alguno sobre quien denuncia.
      </p>
      <p>
        Por eso el registro puede ser público: prueba que algo ocurrió, sin
        revelar quién lo dijo.
      </p>
    </main>
  );
}