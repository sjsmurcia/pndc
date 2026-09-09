import { useState } from "react";

import { Aviso } from "../componentes/Aviso";
import { Boton } from "../componentes/Boton";
import type { NivelIdentidad } from "../componentes/BarraAnonimato";


const OPCIONES: {
    valor: NivelIdentidad;
    titulo: string;
    description: string;

}[] = [
        {
            valor: "anonimo",
            titulo: "Total Anonimato",
            description: "No se guarda ningun dato que permita saber quien envio la denuncia. Solo usted conoce su codigo de seguimiento.",

        },
        {
            valor: "seudonimo",
            titulo: "Seudonimo",
            description: "Se guarda un seudonimo que aparece junto a su caso en el panel de revision. Sigue sin registrarse ningun dato real sobre usted.  ",

        },
        {
            valor: "publico",
            titulo: "Publico voluntario",
            description: "Autoriza a los revisores a citarlo como fuente si el caso avanza. Su denuncia deja de ser anonima frente a ellos.",

        },
    ];
export function SelectorIdentidad({
    actual,
    onElegir,
    onCancelar,
}: {
    actual: NivelIdentidad;
    onElegir: (nivel: NivelIdentidad) => void;
    onCancelar: () => void;
}) {
    const [pendiente, setPendiente] = useState<NivelIdentidad | null>(null);
    const [reconoce, setReconoce] = useState(false);

    const ORDEN: NivelIdentidad[] = ["anonimo", "seudonimo", "publico"];
    const posicionActual = ORDEN.indexOf(actual);

    function seleccionar(nivel: NivelIdentidad) {
        if (nivel === "publico") {
            setPendiente(nivel);
            setReconoce(false);
        } else {
            onElegir(nivel);
        }
    }
    if (pendiente === "publico") {
        return (
            <main style={{ padding: "var(--sp-6) var(--sp-5) var (--sp-8)" }}>
                <h1>Confirmar identidad publica</h1>

                <Aviso nivel="critico" titulo="Este cambio no se puede revertir">
                    <p style={{ margin: "0 0 var(--sp-2)" }}>
                        Una vez que su caso queda marcado como publico, los revisores
                        pueden citarlo como fuente.
                    </p>
                    <p style={{ margin: 0 }}>
                        El portal sigue sin registrar su informacion personal,
                        pero su denuncia deja de ser anonima frente a los revisores.
                    </p>
                </Aviso>

                <label
                    style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "var(--sp-2)",
                        padding: "var(--sp-3) 0",
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
                        Entiendo que el cambio a identidad publica es irreversible
                        y acepto que mi denuncia deja de ser anonima frente a los revisores.
                    </span>
                </label>

                <div style={{ display: "flex", gap: "var(--sp-3)", marginTop: "var(--sp-4)" }}>

                    <Boton variante="secundario" onClick={() => setPendiente(null)}>
                        Volver sin cambiar
                    </Boton>
                    <Boton disabled={!reconoce} onClick={() => onElegir("publico")}>
                        Confirmar identidad publica
                    </Boton>

                </div>
            </main>
        );
    }

    return (
        <main style={{ padding: "var(--sp-6) var(--sp-5) var(--sp-8)" }}>
            <h1>Nivel de Identidad</h1>
            <p style={{ color: "var(--texto-secundario)", marginBottom: "var(--sp-5)" }}>
                Puede aumentar su exposicion en cualquier momento.
            </p>
            <div style={{ display: "grid", gap: "var(--sp-3)", marginBottom: "var(--sp-5)" }}>
                {OPCIONES.map((opcion, indice) => {
                    const esActual = opcion.valor === actual;
                    const retrocede = indice < posicionActual;
                    return (
                        <div
                            key={opcion.valor}
                            style={{
                                border: `1px solid ${esActual ? "var(--c-navy-70)" : "var(--borde)"}`,
                                borderLeft: esActual
                                    ? "6px solid var(--c-navy-70)"
                                    : "1px solid var(--sp-4)",
                                padding: "var(--sp-4)",
                                opacity: retrocede ? 0.5 : 1,
                            }}
                        >
                            <h2 style={{ fontSize: 19, marginBottom: "var(--sp-1)" }}>
                                {opcion.titulo}
                                {esActual && (
                                    <span
                                        style={{
                                            fontSize: 14,
                                            fontWeight: 400,
                                            color: "var(--texto-secundario)",
                                            marginLeft: "var(--sp-2)",

                                        }}
                                    >
                                        Nivel Actual
                                    </span>
                                )}
                            </h2>
                            <p style={{ fontSize: 15, marginBottom: "var(--sp-3)" }}>
                                {opcion.description}
                            </p>
                            {retrocede ? (
                                <p
                                    style={{
                                        fontSize: 14,
                                        color: "var(--texto-secundario)",
                                        margin: 0,
                                    }}
                                >No disponible: no se puede reducir la exposicion ya elegida
                                </p>
                            ) : (
                                !esActual && (
                                    <Boton
                                        variante="secundario"
                                        onClick={() => seleccionar(opcion.valor)}
                                    >
                                        Elegir {opcion.titulo.toLowerCase()}
                                    </Boton>
                                )
                            )}
                        </div>
                    );
                })}
            </div>
            <Boton variante="texto" onClick={onCancelar}>
                Volver al asistente
            </Boton>
        </main>
    );
}