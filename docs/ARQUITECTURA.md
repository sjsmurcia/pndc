# Arquitectura y decisiones de diseño

Este documento explica **por qué** el sistema está construido así. Las
decisiones que aparecen aquí se tomaron de forma deliberada y varias
descartan alternativas más habituales.

---

## 1. El principio que ordena todo lo demás

**Quien denuncia no arriesga nada; quien revisa responde por todo.**

De ahí salen dos modelos de identidad opuestos dentro del mismo sistema:

| | Denunciante | Revisor |
|---|---|---|
| Identidad | Anónimo por diseño | Plenamente identificado |
| Autenticación | Un código del que solo existe el hash | Usuario y contraseña |
| Registro de actividad | Ninguno que lo identifique | Cada acción en la bitácora |
| Rendición de cuentas | Ninguna: es el propósito | Total |

Esa asimetría no es una curiosidad: es el criterio que resuelve casi todas
las decisiones que siguen.

---

## 2. Estilo arquitectónico

Backend monolítico modular en capas, frontend desacoplado que consume una
API REST versionada, y **un solo componente separado por seguridad**: el
saneador de archivos.

No se adoptan microservicios. No hay requisitos de escalado independiente
que los justifiquen, y la cadena de hashes se sostiene mejor con
transacciones dentro de una sola base de datos.

### Capas del backend

| Capa | Contenido | Regla |
|---|---|---|
| API (routers) | Endpoints v1, validación de entrada, control de rol | No contiene lógica de negocio |
| Esquemas (Pydantic) | Contratos de entrada y salida | Generan el OpenAPI, del que sale el cliente TypeScript |
| Servicios de dominio | Cadena, saneadores, triaje, marca, códigos, anti-spam | No conocen HTTP |
| Persistencia | Modelos SQLAlchemy y migraciones Alembic | Único punto de acceso a la base |

---

## 3. Dos roles de base de datos

Es la decisión que hace **verificable** la inmutabilidad de la bitácora, y
no un detalle de configuración.

| Rol | Uso | Privilegios |
|---|---|---|
| `pndc_owner` | Migraciones (Alembic) | Dueño del esquema, DDL |
| `pndc_app` | La aplicación (FastAPI) | Solo datos, sin DDL |
| `pndc_verificador` | Verificador independiente | Solo `SELECT` sobre `bitacora` |

Sobre esa separación se apoya la migración `0009`:

```sql
REVOKE UPDATE, DELETE ON bitacora FROM pndc_app;

CREATE RULE bitacora_no_update AS ON UPDATE TO bitacora DO INSTEAD NOTHING;
CREATE RULE bitacora_no_delete AS ON DELETE TO bitacora DO INSTEAD NOTHING;
```

Si la API se conectara con el rol propietario, ese `REVOKE` sería
decorativo: un rol con DDL se devuelve los permisos con una línea de SQL.

**Dos defensas independientes.** El `REVOKE` protege contra la aplicación;
las reglas del motor protegen contra cualquiera, incluido el propietario y
un superusuario. Se puede comprobar:

```sql
-- Como pndc_owner, que además es superusuario en el contenedor:
DELETE FROM bitacora;
-- Resultado: DELETE 0
```

Alterar el registro exige un `DROP RULE`, es decir privilegios de
estructura. Acceso a los datos no basta.

Una consecuencia práctica: las reglas se evalúan **antes** que los
privilegios, así que el intento devuelve `DELETE 0` en vez de
`permission denied`. La protección funciona de forma silenciosa.

---

## 4. La cadena de hashes

Cada evento de la bitácora guarda el hash del anterior:

```
hash_actual = SHA256(tipo_evento | payload_canónico | hash_anterior)
```

El payload se serializa de forma **canónica**: claves ordenadas, sin
espacios, UTF-8 real. Sin eso, dos serializaciones del mismo diccionario
producirían hashes distintos y la cadena quedaría inválida sin que nadie
la tocara.

`creado_en` **no** entra en el hash: lo pone PostgreSQL con `now()` en el
momento del INSERT, así que la aplicación no lo conoce al calcular.
Incluirlo obligaría a fijar la fecha desde Python, y entonces el instante
lo controlaría el cliente en vez del motor.

### El índice no es la garantía

`bitacora.indice` es informativo. Las secuencias de PostgreSQL no son
transaccionales, así que un INSERT revertido consume un número y deja un
hueco permanente que parecería un borrado. **La integridad la sostiene la
cadena de hashes, no la numeración.**

Se consideró calcular el índice en la aplicación con `SELECT ... FOR UPDATE`
para garantizar consecutividad, y se descartó: serializaría todas las
escrituras a la bitácora a cambio de una segunda defensa redundante.

### El verificador es un programa aparte

Si la verificación viviera dentro de la misma API que escribe la bitácora,
verificarse a sí misma no probaría nada. El verificador se ejecuta por
separado, con su propio rol de solo lectura, y **reimplementa** el cálculo
del hash en vez de importarlo: un cambio malicioso en el servicio de cadena
pasaría desapercibido en ambos lados si compartieran código.

---

## 5. Saneamiento de archivos

Cada formato delata a su autor de una manera distinta.

| Formato | Qué delata | Cómo se sanea |
|---|---|---|
| Imágenes | GPS, fecha, marca, modelo y número de serie del equipo. La miniatura incrustada a veces conserva la foto **antes** de editarla. | Se construye una imagen nueva con los píxeles del original. Todo lo que no sea un píxel queda fuera por construcción. |
| PDF | Autor y software. El texto tapado con un rectángulo negro sigue siendo seleccionable. Historial incremental con versiones previas. | Rasterización: cada página se convierte en imagen y el documento se reconstruye. Lo que estaba debajo del recuadro deja de existir. |
| Office | Es un ZIP: autor, todos los que editaron, control de cambios, texto borrado que permanece dentro, y la ruta del disco con el nombre real del usuario. | **Fuera de alcance.** Se rechazan en la lista blanca. |

### Cuatro reglas del saneador

1. **Lista blanca, nunca lista negra.** Una lista negra tendría que
   anticipar todo lo peligroso, y siempre falta algo.
2. **Los bytes, no la extensión.** La extensión la elige quien sube el
   archivo; renombrar un ejecutable a `.jpg` es trivial.
3. **El original se destruye.** Y de hecho nunca toca el disco: llega en
   memoria, se sanea en memoria, y solo se escribe la versión limpia.
4. **El saneador corre aislado.** Procesa archivos no confiables con
   librerías que analizan formatos complejos, que es donde aparecen las
   vulnerabilidades de ejecución de código.

### El aislamiento, en el compose

```yaml
sanitizer:
  network_mode: "none"
  read_only: true
  cap_drop: ["ALL"]
  security_opt: [no-new-privileges:true]
  volumes: [quarantine:/var/quarantine]
```

Sin red, sin credenciales, sin base de datos. Su único canal con el resto
del sistema es un volumen compartido. Si un archivo malicioso comprometiera
el proceso, no encontraría nada que exfiltrar ni por dónde salir.

> **Diferencia entre diseño e implementación.** El servicio está declarado
> y configurado con aislamiento completo, pero el saneamiento se ejecuta
> hoy dentro del contenedor `api`. Moverlo requiere una cola de trabajo
> entre procesos, pendiente de un sprint posterior.

---

## 6. Trazabilidad de la evidencia

Cada copia entregada a un revisor es **distinta**. Se incrusta un patrón
derivado de un UUID único en el bit menos significativo del canal azul de
cada píxel: cambiar un valor de 128 a 129 en azul es invisible para el ojo
y perfectamente legible para un programa.

Si un archivo se filtra, se extrae la huella y se consulta en
`GET /revision/auditoria/marca/{marca_id}`, que devuelve quién lo descargó,
cuándo y con qué justificación.

La justificación es **obligatoria** y de al menos veinte caracteres: si un
revisor tiene que escribir por qué necesita el archivo, la descarga por
curiosidad deja de ser gratuita.

---

## 7. Anti-spam sin identificar a nadie

Tres capas, ninguna recurre a servicios de terceros.

**Honeypot.** Campo de formulario invisible para personas. Si viene relleno,
es un bot rellenando todo lo que encuentra. Cuesta cero.

**Prueba de trabajo.** El navegador debe encontrar un `nonce` que produzca
un SHA-256 con cuatro ceros iniciales. Unos 65 mil intentos: medio segundo
para quien denuncia una vez, horas de CPU para quien intente mil envíos. La
asimetría es el punto: calcular cuesta, verificar es instantáneo.

El reto va firmado con HMAC y el servidor no guarda nada; toda la
información viaja dentro del propio reto.

**Rate limit efímero.** Contador en memoria que se pierde al reiniciar. Es
un límite **del formulario**, no por persona: limitar por persona exigiría
identificarla. La función `registrar_envio()` no recibe parámetros, así que
es imposible pasarle una IP aunque alguien quisiera.

---

## 8. Alternativas descartadas

### reCAPTCHA

Es un servicio de Google: cada visitante del formulario contactaría sus
servidores, que recibirían su IP y podrían correlacionarla con su sesión de
Google. El portal no guardaría ese dato, pero **se lo entregaría a un
tercero**, lo cual contradice su propósito. Además penaliza a usuarios de
VPN y Tor, y resulta hostil para personas con discapacidad visual.

Es la misma decisión que toman SecureDrop y GlobaLeaks. Y el mismo criterio
llevó a auto-hospedar las fuentes tipográficas en vez de cargarlas desde
Google Fonts.

### MongoDB

Sin transacciones multidocumento por defecto ni integridad referencial, no
puede sostener una cadena de hashes ni las relaciones entre denuncias,
evidencias y revisiones.

### Cifrado extremo a extremo

Al operador **sí** se le confía leer las denuncias, porque sus revisores
deben hacerlo; lo que no se le confía es alterarlas o borrarlas sin dejar
rastro. Cifrar el contenido con las claves públicas de los revisores, como
hace GlobaLeaks, es alcance adicional y no un requisito del modelo
planteado.

### Custodia legal de los archivos originales

Se consideró conservar el original con sus metadatos bajo llave, entregable
solo con orden judicial. Se descartó, y la razón no es técnica:

**Lo que puede entregarse, puede exigirse.** Si el original con GPS existe
en algún lugar, entonces existe: una orden judicial lo saca, un empleado
con acceso lo saca, un ataque al proveedor lo saca. Y quien sepa que existe
puede presionar para obtenerlo.

Hoy, si un juez pide el original de una evidencia, la respuesta es *no
existe*, y es completa y verificable. Con custodia, la respuesta sería *sí
existe, aquí está*, y el denunciante quedaría identificado por el GPS de su
propia foto en el peor momento posible: cuando su denuncia empezó a
molestar a alguien.

Lo que sí se conserva bajo custodia estricta es la evidencia **saneada**,
que mantiene íntegro lo que la imagen muestra. Lo único que se pierde es la
huella del equipo de quien la tomó, que no es evidencia del hecho
denunciado sino de quién lo reportó.

### Seudónimo elegido por el usuario

El seudónimo lo genera el servidor. Un apodo elegido a mano suele ser el
mismo que la persona usa en otros sitios, y eso lo convierte en una huella
que cruza sistemas. Hay una prueba automatizada que falla si alguien
decide permitir que el usuario lo escriba.

### Sesión con JWT

Se eligió sesión en base de datos. Un JWT no se puede revocar antes de que
expire, y en un portal donde un revisor con acceso a denuncias sin redactar
puede ser dado de baja, la revocación inmediata pesa más que ahorrar una
consulta. Mantener una lista negra de tokens sería reinventar la misma
tabla que se estaba evitando.

La cookie es `HttpOnly` (inaccesible desde JavaScript, así que un XSS no la
roba) y `SameSite=Strict` (resuelve CSRF sin token adicional).

---

## 9. Criptografía empleada

El proyecto usa **funciones hash, no cifrado**. Un hash es una huella
irreversible, útil para comprobar integridad y guardar secretos sin poder
recuperarlos. El cifrado es reversible y sirve para confidencialidad.

| Uso | Función | Por qué esa |
|---|---|---|
| Bitácora | SHA-256 encadenado | Rápido y suficiente: no hay secreto que proteger, solo integridad |
| Código de seguimiento | Argon2id | Es un secreto tipo contraseña: hace falta un hash **lento** y con sal |
| Contraseñas de revisor | Argon2id | Igual |
| Token de sesión | SHA-256 | El token ya son 256 bits aleatorios, no hay nada que adivinar |
| Evidencia | SHA-256 | Prueba que lo almacenado es lo recibido |
| Prueba de trabajo | SHA-256 | Debe ser rápido de verificar y costoso de resolver |

**Regla aplicada sin excepción:** no se escribe criptografía propia. Se
emplean `hashlib` de la librería estándar y `argon2-cffi` con sus
parámetros por defecto, que siguen la RFC 9106. Ajustarlos a ojo sería la
misma clase de error que escribir criptografía propia.

---

## 10. Límites declarados

Estos límites existen y no se resuelven. Declararlos vale más que fingir
que el sistema cubre todo.

**La huella del sensor de la cámara (PRNU).** Permite vincular fotografías
tomadas con un mismo equipo incluso después de eliminar todos los
metadatos. Anularla es materia de investigación avanzada.

**La marca de evidencia no resiste recompresión agresiva.** El patrón en el
bit menos significativo sobrevive a una copia, pero no a reescalar y volver
a comprimir con pérdida. Es trazabilidad razonable y disuasión, no una
marca inviolable.

**El código de seguimiento no se recupera.** Sin correo asociado, quien lo
pierde pierde el acceso a su caso para siempre. La denuncia sigue su curso,
pero esa persona ya no puede ampliarla ni responder al revisor. Es
consecuencia directa del anonimato, no un descuido.

**No hay notificaciones.** Un correo, un SMS o un push requieren una
dirección, y esa dirección identifica. El modelo es *pull*: el revisor deja
su pregunta y quien denuncia la ve cuando vuelve con su código. Si nunca
vuelve, el revisor decide con lo que tiene.

**El seguimiento hace búsqueda lineal.** Argon2 usa sal aleatoria, así que
el mismo código produce hashes distintos y no se puede indexar. Hay que
verificar denuncia por denuncia. La alternativa sería guardar además un
hash rápido determinista, pero eso reintroduce el riesgo de fuerza bruta
que Argon2 evita.

**El texto publicado no se puede editar desde la aplicación.** Una vez
publicado un caso, corregir su redacción exige acceso a la base. Un flujo
de corrección con su propio registro en bitácora queda como trabajo
pendiente.

**No se puede impedir que alguien envíe basura.** Solo se puede impedir que
la basura se publique. Cien denuncias falsas contra una institución no
mueven el conteo público, porque nada llega al portal sin que un revisor lo
apruebe y un supervisor lo publique. El costo del ataque recae en el equipo
de revisión, no en la integridad del portal.

**La consulta de auditoría no se registra.** Un supervisor consultando quién
descargó qué no deja rastro en la bitácora. Registrar cada acceso llenaría
la cadena de ruido, pero implica que el supervisor tiene un punto ciego
sobre su propia actividad de consulta.

---

## 11. Modelo de datos

Doce tablas en cuatro dominios: denuncias, revisión, custodia de evidencia
e integridad. Ver el diagrama entidad-relación en la documentación de
modelado.

### Lo que deliberadamente no existe

No hay tabla de denunciantes. No hay columnas de dirección IP, correo
electrónico, teléfono, huella de navegador ni identidad. Del código de
seguimiento solo se almacena su hash Argon2.

El anonimato no es una promesa del reglamento: es una **propiedad del
esquema**, auditable por cualquiera que inspeccione la estructura. Y hay
una prueba automatizada que recorre todas las tablas y falla si aparece una
columna sospechosa.
