# PNDC — Portal Nacional de Denuncias de Corrupción

Portal donde cualquier persona puede denunciar corrupción sin revelar su
identidad, adjuntar evidencia saneada de metadatos y dar seguimiento a su
caso sin crear una cuenta. Publica versiones redactadas de los casos y un
conteo por institución.

> **Ejercicio académico.** El sistema se valida con denuncias sintéticas e
> instituciones ficticias. No opera un canal real de denuncias. El término
> «Nacional» indica alcance geográfico simulado, no una entidad de gobierno.

El diseño se resume en una frase: **quien denuncia no arriesga nada; quien
revisa responde por todo.**

---

## Puesta en marcha

Requisitos: Docker Desktop con WSL2, Python 3.12 y Node 20 o superior.

```powershell
git clone https://github.com/sjsmurcia/pndc.git
cd pndc
Copy-Item .env.example .env
```

**Backend y base de datos:**

```powershell
docker compose up -d --build db api
```

**Migraciones** (con entorno virtual local):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
alembic upgrade head
```

**Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

| Servicio | Dirección |
|---|---|
| Portal | http://localhost:5173 |
| API y documentación | http://localhost:8001/docs |
| PostgreSQL | localhost:5433 |

La API se publica en el 8001 y la base en el 5433 para no chocar con
instalaciones existentes en los puertos habituales.

---

## Datos de demostración

La migración `0014` siembra 20 denuncias sintéticas en distintos estados,
con su cadena de eventos de bitácora correspondiente. **No se aplica por
defecto**: el portal arranca vacío en un entorno limpio.

```powershell
$env:PNDC_SEMILLA_DEMO = "1"
cd backend
alembic upgrade head
```

Los códigos de seguimiento de esos casos no existen: fueron sembrados
directamente en la base y no se pueden consultar desde el portal.

### Revisores de prueba

Credenciales incluidas en la migración `0012`. Son deliberadamente débiles:
el portal es un ejercicio académico con datos sintéticos y las credenciales
deben estar documentadas para que la demostración funcione. En un despliegue
real irían por variable de entorno y con cambio obligatorio en el primer
acceso.

| Usuario | Contraseña | Rol |
|---|---|---|
| `ana.reyes` | `revisor123` | revisor |
| `luis.mora` | `revisor123` | revisor |
| `marta.solis` | `supervisor123` | supervisor |

---

## Verificar la integridad del registro

El verificador es un programa **independiente** del portal. Se conecta con
un rol que solo puede leer y recalcula la cadena de hashes desde cero, sin
confiar en nada que la aplicación afirme.

```powershell
cd backend\verificador
python verificar.py
```

Salida esperada con la cadena intacta:

```
ESTADO: CADENA INTACTA
Eventos verificados: 90
```

Si algún registro fue alterado o eliminado, indica el índice exacto del
evento donde la cadena deja de cuadrar.

Para integrarlo en otra herramienta: `python verificar.py --json`. El código
de salida es 1 si la cadena está rota.

---

## Pruebas

```powershell
cd backend
pytest -q
```

80 pruebas sobre los servicios críticos: cadena de hashes, saneadores de
imagen y PDF, detección de tipo por bytes de cabecera, generación de códigos,
anti-spam, y auditoría del esquema contra fugas de identidad.

Esa última merece atención: `tests/test_auditoria_identidad.py` falla si
alguien agrega una columna de IP, mete el relato en un payload público o
quita la bandera que desactiva los logs de acceso. Convierte el principio
del proyecto en algo que el código verifica solo.

---

## Estructura

```
backend/
  app/
    api/v1/        endpoints por área funcional
    core/          configuración tipada desde .env
    db/            base declarativa y sesión
    models/        12 tablas en SQLAlchemy
    schemas/       contratos Pydantic, generan el OpenAPI
    services/      lógica de dominio sin dependencia de HTTP
  alembic/         migraciones versionadas
  verificador/     programa independiente de verificación
  tests/
frontend/
  src/
    api/           cliente tipado generado desde OpenAPI
    componentes/   piezas compartidas
    paginas/       las cuatro vistas del portal
    estilos/       tokens del sistema de diseño
sanitizer/         proceso aislado, sin red ni credenciales
docs/              arquitectura y despliegue
```

---

## Documentación

- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) — decisiones de diseño,
  alternativas descartadas y límites declarados.
- [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md) — procedimiento de despliegue
  en Azure y configuración de privacidad.
- [`docs/CONVENCION_COMMITS.md`](docs/CONVENCION_COMMITS.md) — formato de
  los mensajes de commit.

---

## Licencia y alcance

Proyecto académico de Ingeniería de Software. Todo el software empleado es
de código abierto. El sistema es auto-hospedable a propósito: una plataforma
de denuncias que solo pueda operar sobre la infraestructura de un proveedor
concreto traslada a ese proveedor parte de la confianza que el diseño busca
eliminar.

Desarrollado por Jessel Murcia.
