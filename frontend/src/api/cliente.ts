import type { paths } from "./tipos";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8001";
/*extrae del openapi el tipo de una respuesta correcta */
/** Extrae del OpenAPI el tipo del cuerpo de una peticion. */
type Cuerpo<T> = T extends {
  requestBody: { content: { "application/json": infer C } };
}
  ? C
  : never;
type Respuesta<T> = T extends { responses: infer R }
  ? R extends { 200: { content: { "application/json": infer C } } }
    ? C
    : R extends { 201: { content: { "application/json": infer C } } }
      ? C
      : never
  : never;

export class ErrorApi extends Error {
  constructor(
    readonly estado: number,
    mensaje: string,
  ) {
    super(mensaje);
  }
}
async function peticion<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const respuesta = await fetch(`${BASE}${ruta}`, {
    ...opciones,
    headers: {
      "Content-Type": "application/json",
      ...opciones.headers,
    },
  });

  if (!respuesta.ok) {
    //el backend devuelve {detalle}
    const cuerpo = await respuesta.json().catch(() => ({}));
    throw new ErrorApi(
      respuesta.status,
      cuerpo.detail ?? "No se pudo completar la operacion",
    );
  }
  return respuesta.json();
}
//denuncias

type CrearDenuncia = paths["/api/v1/denuncias"]["post"];
export function crearDenuncia(datos: Cuerpo<CrearDenuncia>) {
  return peticion<Respuesta<CrearDenuncia>>("/api/v1/denuncias", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

//subida de informacion con multipart
export async function subirEvidencia(
  denunciaId: number,
  codigo: string,
  archivo: File,
) {
  const formulario = new FormData();
  formulario.append("codigo", codigo);
  formulario.append("archivo", archivo);

  const respuesta = await fetch(
    `${BASE}/api/v1/denuncias/${denunciaId}/evidencias`,
    { method: "POST", body: formulario },
  );

  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}));
    throw new ErrorApi(
      respuesta.status,
      cuerpo.detail ?? "No se pudo adjuntar el archivo",
    );
  }
  return respuesta.json();
}
//seguimiento

type ConsultarCaso = paths["/api/v1/seguimiento"]["post"];

export function consultarCaso(codigo: string) {
  return peticion<Respuesta<ConsultarCaso>>("/api/v1/seguimiento", {
    method: "POST",
    body: JSON.stringify({ codigo }),
  });
}

type EscribirMensaje = paths["/api/v1/seguimiento/mensajes"]["post"];

export function escribirMensaje(codigo: string, cuerpo: string) {
  return peticion<Respuesta<EscribirMensaje>>("/api/v1/seguimiento/mensajes", {
    method: "POST",
    body: JSON.stringify({ codigo, cuerpo }),
  });
}

//catalogo
type ObtenerCatalogo = paths["/api/v1/catalogo"]["get"];

export function obtenerCatalogo() {
  return peticion<Respuesta<ObtenerCatalogo>>("/api/v1/catalogo");
}

type ObtenerReto = paths["/api/v1/denuncias/reto"]["get"];

export function obtenerReto() {
  return peticion<Respuesta<ObtenerReto>>("/api/v1/denuncias/reto");
}

// --- Publico ---
//
// Estos dos endpoints no declaran response_model en FastAPI, asi que el
// OpenAPI no lleva su esquema de respuesta y el tipo generado sale vacio.
// Se tipan a mano hasta que el backend los declare.

type RankingRespuesta = {
  titulo: string;
  aclaracion: string;
  instituciones: { nombre: string; tipo: string; casos: number }[];
  categorias: { nombre: string; casos: number }[];
};

export function obtenerRanking() {
  return peticion<RankingRespuesta>("/api/v1/publico/ranking");
}

type CasoPublicadoRespuesta = {
  caso_id: number;
  categoria: string;
  institucion: string;
  tipo_institucion: string;
  gravedad: string | null;
  texto: string;
  publicado_en: string;
};

export function obtenerCasosPublicados() {
  return peticion<CasoPublicadoRespuesta[]>("/api/v1/publico/casos");
}

type EstadoCadenaRespuesta = {
  intacta: boolean;
  eventos: number;
  indice_roto: number | null;
  advertencia: string;
};

export function obtenerEstadoCadena() {
  return peticion<EstadoCadenaRespuesta>("/api/v1/publico/bitacora/estado");
}