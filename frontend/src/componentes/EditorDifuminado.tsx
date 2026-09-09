import { useEffect, useRef, useState } from "react";

import { Aviso } from "./Aviso";
import { Boton } from "./Boton";

type Region = {
    x: number;
    y: number;
    ancho: number;
    alto: number;
};

const TAMANO_BLOQUE = 12; //pixeles del mosaico
const ANCHO_MAXIMO = 640; //del lienzo en la pantalla

/**
 * Editor de difuminado, ocurre en el navegador 
 */

export function EditorDifuminado({
    archivo,
    onGuardar,
    onCancelar,
}: {
    archivo: File;
    onGuardar: (editado: File) => void;
    onCancelar: () => void;
}) {
    const lienzoRef = useRef<HTMLCanvasElement>(null);
    const originalRef = useRef<HTMLImageElement | null>(null);
    const [regiones, setRegiones] = useState<Region[]>([]);
    const [arrastrando, setArrastrando] = useState<Region | null>(null);
    const [escala, setEscala] = useState(1);

    //cargar la imagen original
    useEffect(() => {
        const url = URL.createObjectURL(archivo);
        const imagen = new Image();

        imagen.onload = () => {
            originalRef.current = imagen;
            const factor = Math.min(1, ANCHO_MAXIMO / imagen.width);
            setEscala(factor);

            const lienzo = lienzoRef.current;
            if (!lienzo) return;
            lienzo.width = imagen.width * factor;
            lienzo.height = imagen.height * factor;
            lienzo.getContext("2d")?.drawImage(imagen, 0, 0, lienzo.width, lienzo.height);
            URL.revokeObjectURL(url);
        };
        imagen.src = url;
    }, [archivo]);

    //rehacemos la imagen 

    useEffect(() => {
        const lienzo = lienzoRef.current;
        const imagen = originalRef.current;
        if (!lienzo || !imagen) return;

        const ctx = lienzo.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(imagen, 0, 0, lienzo.width, lienzo.height);

        for (const region of regiones) {
            pixelear(ctx, region)

        }

        if (arrastrando) {
            ctx.strokeStyle = "#f2cb07";
            ctx.lineWidth = 2;
            ctx.setLineDash([6, 4]);
            ctx.strokeRect(
                arrastrando.x,
                arrastrando.y,
                arrastrando.ancho,
                arrastrando.alto
            );
            ctx.setLineDash([]);
        }
    },
        [regiones, arrastrando]);

    function posicion(e: React.MouseEvent<HTMLCanvasElement>) {
        const lienzo = e.currentTarget;
        const caja = lienzo.getBoundingClientRect();

        const factorX = lienzo.width / caja.width;
        const factorY = lienzo.height / caja.height;

        return {
            x: (e.clientX - caja.left) * factorX,
            y: (e.clientY - caja.top) * factorY,
        };

    }



    function empezar(e: React.MouseEvent<HTMLCanvasElement>) {
        const p = posicion(e);
        setArrastrando({ x: p.x, y: p.y, ancho: 0, alto: 0 });
    }
    function mover(e: React.MouseEvent<HTMLCanvasElement>) {
        if (!arrastrando) return;
        const p = posicion(e);
        setArrastrando({
            ...arrastrando,
            ancho: p.x - arrastrando.x,
            alto: p.y - arrastrando.y

        });
    }
    function terminar() {
        if (!arrastrando) return;

        //normalizar arrastres 
        const region: Region = {
            x: Math.min(arrastrando.x, arrastrando.x + arrastrando.ancho),
            y: Math.min(arrastrando.y, arrastrando.y + arrastrando.alto),
            ancho: Math.abs(arrastrando.ancho),
            alto: Math.abs(arrastrando.alto)
        };

        setArrastrando(null);
        if (region.ancho > 8 && region.alto > 8) {
            setRegiones((previas) => [...previas, region]);

        }
    }

    function guardar() {
        const imagen = originalRef.current;
        if (!imagen) return;

        const salida = document.createElement("canvas");
        salida.width = imagen.width;
        salida.height = imagen.height;

        const ctx = salida.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(imagen, 0, 0);
        for (const region of regiones) {
            pixelear(ctx, {
                x: region.x / escala,
                y: region.y / escala,
                ancho: region.ancho / escala,
                alto: region.alto / escala,
            });
        }
        salida.toBlob((blob) => {
            if (!blob) return;
            onGuardar(
                new File([blob], archivo.name, { type: "image/jpeg" })
            );
        }, "image/jpeg", 0.9);
    }

    return (
        <section>
            <h2>Cubrir zonas de la imagen</h2>

            <Aviso nivel="informativo">
                Arrastre sobre la imagen para cubrir rostros, matriculas, firmas o cualquier dato que identifique a alguien.
                y/o donde usted no se exponga o exponga datos donde lo puedan identificar.
            </Aviso>

            <div style={{ marginBottom: "var(--sp-3)" }}>
                <canvas
                    ref={lienzoRef}
                    onMouseDown={empezar}
                    onMouseMove={mover}
                    onMouseUp={terminar}
                    onMouseLeave={terminar}
                    style={{
                        border: "1px solid var(--borde-input)",
                        cursor: "crosshair",
                        maxWidth: "100%",
                        display: "block",
                    }}
                />
            </div>

            <p style={{ fontSize: 14, color: "var(--texto-secundario)" }}>
                {regiones.length === 0
                ? "Ninguna zona cubierta todavia."
                : `${regiones.length} zona${regiones.length > 1 ? "s" : ""} cubierta${regiones.length > 1 ? "s" : ""}.`}
            </p>

            <div style={{ display: "flex", gap: "var(--sp-3)", flexWrap: "wrap" }}>
                <Boton onClick={guardar}>Aplicar y volver</Boton>
                <Boton
                    variante="secundario"
                    onClick={() => setRegiones([])}
                    disabled={regiones.length === 0}
                >Quitar todas las zonas</Boton>
                <Boton variante="texto" onClick={onCancelar}>
                    Cancelar
                </Boton>
            </div>
        </section>
    );
}

//promedio del el color de cada bloque 

function pixelear(ctx: CanvasRenderingContext2D, region: Region) {
   const x=Math.round(region.x);
   const y=Math.round(region.y);
   const ancho=Math.round(region.ancho);
   const alto =Math.round(region.alto); 
   if(ancho <=0 || alto <=0) return; 

    const datos = ctx.getImageData(x, y, ancho, alto);
    const pixeles = datos.data;

    for (let by = 0; by < alto; by += TAMANO_BLOQUE) {
        for (let bx = 0; bx < ancho; bx += TAMANO_BLOQUE) {
            let r = 0;
            let g = 0;
            let b = 0;
            let cuenta = 0;
            const hastaY = Math.min(by + TAMANO_BLOQUE, alto);
            const hastaX = Math.min(bx + TAMANO_BLOQUE, ancho);

            for (let py = by; py < hastaY; py++) {
                for (let px = bx; px < hastaX; px++) {
                    const i = (py * ancho + px) * 4;
                    r += pixeles[i];
                    g += pixeles[i + 1];
                    b += pixeles[i + 2];

                    cuenta++;
                }
            }
            r = Math.round(r / cuenta);
            g = Math.round(g / cuenta);
            b = Math.round(b / cuenta);

            for (let py = by; py < hastaY; py++) {
                for (let px = bx; px < hastaX; px++) {
                    const i = (py * ancho + px) * 4;
                    pixeles[i] = r;
                    pixeles[i + 1] = g;
                    pixeles[i + 2] = b;
                }
            }
        }
    }
    ctx.putImageData(datos, x, y);

}