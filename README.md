# PNDC — Portal Nacional de Denuncias de Corrupcion

Proyecto academico de Ingenieria de Software. No opera con denuncias reales.

## Estructura

    backend/    API en Python (FastAPI, SQLAlchemy, Alembic)
    frontend/   React + Vite + TypeScript
    sanitizer/  Proceso aislado de saneamiento de archivos
    docs/       Documentacion y convenciones

## Convenciones

Ver `docs/CONVENCION_COMMITS.md`.

## Revisores de prueba

Credenciales incluidas en la migracion 0012. Son deliberadamente debiles:
el portal es un ejercicio academico con datos sinteticos y las
credenciales tienen que estar documentadas para que la demostracion
funcione. En un despliegue real irian por variable de entorno y con
cambio obligatorio en el primer acceso.

    ana.reyes     revisor123      revisor
    luis.mora     revisor123      revisor
    marta.solis   supervisor123   supervisor
