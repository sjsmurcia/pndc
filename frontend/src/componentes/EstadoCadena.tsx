import { use, useEffect, useState } from "react";
import { obtenerEstadoCadena } from "../api/cliente";

type Estado = Awaited<ReturnType<typeof obtenerEstadoCadena>>;

export function EstadoCadena() {
    const [estado, setEstado] = useState<Estado | null>(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        obtenerEstadoCadena().then(setEstado).catch(() => setError(true));
    }, []);
    if (error) {
        return (
            <p style={{ fontSize: 14, color: "var(--texto-secundario)", margin: 0 }}>
                No se pudo consultar el estado del registro de integridad.
            </p>
        );
    }
    if (!estado) {
        return (
            <p style={{ fontSize: 14, color: "var(--texto-secundario)", margin: 0 }}>
                Consultando el registro de integridad…
            </p>
        );
    }

    const intacta = estado.intacta;

   return (
    <div
      style={{
        borderLeft: `6px solid ${
          intacta ? "var(--c-green-70)" : "var(--c-red-70)"
        }`,
        border: `1px solid ${intacta ? "var(--c-green-70)" : "var(--c-red-70)"}`,
        borderLeftWidth: 6,
        background: intacta ? "var(--c-green-05)" : "var(--c-red-05)",
        color: intacta ? "var(--c-green-90)" : "var(--c-red-90)",
        padding: "var(--sp-3) var(--sp-4)",
        fontSize: 14,
      }}
    >
      <p style={{ fontWeight: 500, margin: "0 0 var(--sp-1)" }}>
        {intacta
          ? "Registro de integridad sin alteraciones"
          : "El registro de integridad presenta una ruptura"}
      </p>

      <p style={{ margin: "0 0 var(--sp-2)" }}>
        {intacta ? (
          <>
            {estado.eventos} eventos encadenados. Ningún registro fue
            modificado ni eliminado desde que se escribió.
          </>
        ) : (
          <>
            La cadena se rompe en el evento {estado.indice_roto} de{" "}
            {estado.eventos}. Algún registro fue alterado o eliminado
            después de escribirse.
          </>
        )}
      </p>

            <p style={{ margin: 0, fontSize: 13, opacity: 0.85 }}>
        Esta comprobación la hace el propio portal.{" "}
        <a href="/api/v1/publico/bitacora" style={{ color: "inherit" }}>
          Descargue el registro completo
        </a>{" "}
        para verificarlo por su cuenta con una herramienta independiente.
      </p>
    </div>
   );


}