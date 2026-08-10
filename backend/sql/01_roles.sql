-- 01_roles.sql
-- Ejecutar UNA VEZ, como superusuario, conectado a la base "postgres".

-- Estado inicial: que identidades existen en el motor.
SELECT rolname, rolsuper, rolcreatedb, rolcanlogin
FROM pg_roles
WHERE rolcanlogin;

-- Dueno del esquema. Unico que corre migraciones (DDL).
CREATE ROLE pndc_owner LOGIN PASSWORD 'pndc_dev';

-- Rol de la aplicacion: con este se conecta FastAPI.
-- Sin superusuario y sin rolcreatedb: puede modificar DATOS pero no
-- ESTRUCTURA, y no puede alterar permisos. De ahi depende que el REVOKE
-- sobre la bitacora sea irreversible desde la aplicacion.
CREATE ROLE pndc_app LOGIN PASSWORD 'pndc_app_dev';

-- Base del proyecto. El OWNER es pndc_owner: postgres solo ejecuta la
-- sentencia, no queda como dueno.
CREATE DATABASE pndc OWNER pndc_owner;
