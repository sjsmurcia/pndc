/**
 * Prueba de trabajo en el navegador.
 *
 * Busca por fuerza bruta un nonce que produzca un hash SHA-256 con N
 * ceros iniciales. Para quien denuncia una vez son unos segundos; para
 * quien intente mil envios automatizados, horas de CPU.
 *
 * Encarece el envio masivo sin identificar a nadie, que es lo que
 * descarto reCAPTCHA.
 */

async function sha256(texto: string): Promise<string> {
  const datos = new TextEncoder().encode(texto);
  const buffer = await crypto.subtle.digest("SHA-256", datos);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function resolverReto(
  reto: string,
  ceros: number,
  onProgreso?: (intentos: number) => void,
): Promise<string> {
  const objetivo = "0".repeat(ceros);
  let nonce = 0;

  while (true) {
    const candidato = String(nonce);
    const hash = await sha256(`${reto}${candidato}`);

    if (hash.startsWith(objetivo)) {
      return candidato;
    }

    nonce++;

    // Cede el control cada mil intentos para que la interfaz no se
    // congele mientras calcula.
    if (nonce % 1000 === 0) {
      onProgreso?.(nonce);
      await new Promise((r) => setTimeout(r, 0));
    }
  }
}