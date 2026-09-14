# Despliegue

Este documento cubre dos escenarios: el despliegue local con Docker Compose,
que es el utilizado para la demostración, y el procedimiento diseñado para
Azure.

> **Estado del despliegue en Azure.** Diseñado y documentado, **no
> ejecutado**. La demostración se realiza en local. Las razones están al
> final de este documento.

---

## 1. Despliegue local

Es el modo soportado y verificado. El sistema es auto-hospedable a
propósito: una plataforma de denuncias que solo pueda operar sobre la
infraestructura de un proveedor concreto traslada a ese proveedor parte de
la confianza que el diseño busca eliminar.

### Requisitos

- Docker Desktop con WSL2 habilitado
- Python 3.12 (no 3.13 ni superior: varias dependencias binarias todavía
  no publican wheels para versiones más recientes)
- Node 20 o superior

### Procedimiento

```powershell
git clone https://github.com/sjsmurcia/pndc.git
cd pndc
Copy-Item .env.example .env

docker compose up -d --build db api

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
alembic upgrade head
```

Las migraciones se ejecutan desde el entorno local y no desde el contenedor,
con el rol `pndc_owner`. Ver el apartado de roles en `ARQUITECTURA.md`.

### Puertos

| Puerto | Servicio | Nota |
|---|---|---|
| 5173 | Frontend (Vite) | Si está ocupado, Vite salta al 5174 |
| 8001 | API | Deliberadamente no el 8000, para no chocar |
| 5433 | PostgreSQL | Deliberadamente no el 5432 |

Si Vite arranca en el 5174, el CORS del backend ya lo contempla. Ambos
orígenes están en la lista de `allow_origins` de `app/main.py`.

### Reconstruir desde cero

```powershell
docker compose down -v
docker compose up -d db
cd backend
alembic upgrade head
```

`down -v` borra los volúmenes, así que se pierden todos los datos. Los
roles de base de datos y los catálogos se regeneran solos: los scripts de
`backend/sql/docker/` los ejecuta la imagen de PostgreSQL al inicializar
un volumen vacío, y las semillas están en las migraciones.

---

## 2. Configuración de privacidad

Este apartado es parte del diseño, no de la operación.

### Logs de acceso desactivados

Uvicorn escribe por defecto una línea por petición **con la IP del
cliente**. En un portal cuyo argumento central es que no se guarda la IP de
quien denuncia, ese log sería la primera filtración.

En el `Dockerfile`:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000",
     "--reload", "--no-access-log", "--proxy-headers"]
```

Hay una prueba automatizada que lee el `Dockerfile` y falla si alguien quita
esa bandera: `test_uvicorn_corre_sin_access_log` en
`tests/test_auditoria_identidad.py`.

### Bandera explícita en la configuración

```python
class Settings(BaseSettings):
    # Nunca se registran IPs. La bandera existe para que la ausencia sea
    # explícita y verificable en la configuración, no solo en el código.
    registrar_ip: bool = False
```

No la lee nadie: existe para que la decisión sea inspeccionable y para que
una prueba pueda comprobarla.

### Sin llamadas a terceros desde el navegador

Las fuentes tipográficas (Source Sans 3 e IBM Plex Mono) se sirven desde el
propio dominio mediante `@fontsource`, no desde Google Fonts. Cargarlas
desde un CDN haría que cada visitante contactara un servidor externo que
recibiría su IP.

Es el mismo criterio que descartó reCAPTCHA.

---

## 3. Despliegue en Azure (diseñado, no ejecutado)

### Recursos

| Componente | Servicio | Plan | Costo aproximado |
|---|---|---|---|
| Backend | App Service | F1 (gratuito) | 0 USD |
| Base de datos | PostgreSQL Flexible Server | Burstable B1ms | ~15 USD/mes |
| Evidencia | Blob Storage con inmutabilidad | Hot, políticas WORM | Centavos |
| Frontend | Static Web Apps | Gratuito | 0 USD |

Grupo de recursos `rg-pndc`, región East US 2, con límite de gasto activo.

### Procedimiento

**1. Grupo de recursos y base de datos**

```bash
az group create --name rg-pndc --location eastus2

az postgres flexible-server create \
  --resource-group rg-pndc \
  --name pndc-db \
  --tier Burstable --sku-name Standard_B1ms \
  --version 17 \
  --storage-size 32 \
  --public-access 0.0.0.0
```

**2. Roles y migraciones**

Los scripts de `backend/sql/` crean los roles. A diferencia del entorno
local, en Azure el usuario administrador **no** es superusuario, así que
hay que revisar que los `GRANT` funcionen con sus privilegios.

```bash
psql "host=pndc-db.postgres.database.azure.com ..." -f backend/sql/01_roles.sql
psql "... dbname=pndc" -f backend/sql/02_permisos.sql

MIGRATION_DATABASE_URL="postgresql+psycopg://..." alembic upgrade head
```

**3. Almacenamiento inmutable para evidencia**

```bash
az storage account create \
  --name pndcevidencia --resource-group rg-pndc \
  --sku Standard_LRS --kind StorageV2

az storage container-rm create \
  --storage-account pndcevidencia --name evidencias

az storage container immutability-policy create \
  --account-name pndcevidencia --container-name evidencias \
  --period 365
```

La política WORM impide sobrescribir o borrar un blob durante el periodo
definido. Es lo que hace que la evidencia saneada sea tan inalterable como
la bitácora.

**4. App Service**

```bash
az appservice plan create --name plan-pndc --resource-group rg-pndc --sku F1 --is-linux
az webapp create --resource-group rg-pndc --plan plan-pndc --name pndc-api --runtime "PYTHON:3.12"
```

**5. Desactivar los logs de IP en App Service**

Este paso es obligatorio y equivale al `--no-access-log` local:

```bash
az webapp log config \
  --resource-group rg-pndc --name pndc-api \
  --web-server-logging off \
  --detailed-error-messages false \
  --failed-request-tracing false
```

`--web-server-logging off` es el que importa: los logs HTTP de App Service
registran la IP de origen de cada petición.

Además hay que **no habilitar Application Insights**, que recopila
telemetría con datos de cliente por defecto.

**6. Variables de entorno**

```bash
az webapp config appsettings set \
  --resource-group rg-pndc --name pndc-api \
  --settings \
    DATABASE_URL="postgresql+psycopg://pndc_app:...@pndc-db.postgres.database.azure.com/pndc" \
    PNDC_ENV="prod"
```

**No** se define `PNDC_SEMILLA_DEMO`: las denuncias sintéticas son para
demostración local.

**7. Frontend**

```bash
cd frontend
npm run build
az staticwebapp create --name pndc-portal --resource-group rg-pndc
```

Con `VITE_API_URL` apuntando al App Service, y añadiendo ese origen a
`allow_origins` en `app/main.py`.

### Lista de comprobación antes de publicar

- [ ] Logs del servidor web desactivados
- [ ] Application Insights **no** habilitado
- [ ] Contraseñas de revisor cambiadas (las de la migración `0012` son de demostración)
- [ ] `PNDC_SEMILLA_DEMO` sin definir
- [ ] `PNDC_ENV=prod`, para que la cookie de sesión salga con `secure=True`
- [ ] Política de inmutabilidad activa en el contenedor de evidencias
- [ ] HTTPS obligatorio: `az webapp update --https-only true`
- [ ] Verificador ejecutado contra la base de producción con `pndc_verificador`

---

## 4. Por qué el despliegue no se ejecutó

**La demostración no gana nada.** El mismo conjunto de imágenes y las mismas
migraciones corren igual en local. Varios de los momentos clave se
demuestran mejor con acceso directo a la base: romper la bitácora con un
`DROP RULE`, ejecutar el verificador con el rol de solo lectura, extraer la
marca de una imagen descargada.

**El costo no se justifica.** PostgreSQL Flexible en su plan más económico
ronda los 15 USD al mes. Con crédito educativo limitado, mantenerlo activo
durante semanas para una base sin tráfico consume el presupuesto sin aportar
nada.

**Y hay una razón de diseño.** El sistema es auto-hospedable a propósito. Un
portal de denuncias que dependa de un proveedor concreto traslada a ese
proveedor parte de la confianza que el diseño busca eliminar. Demostrarlo
funcionando en local es coherente con ese argumento, no una limitación.
