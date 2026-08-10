-- 02_permisos.sql
-- Ejecutar conectado a la base "pndc", como superusuario.
-- Los permisos de esquema viven dentro de cada base: desde "postgres"
-- estas sentencias no aplican.

-- Lo minimo para que la aplicacion abra conexion y vea el esquema.
GRANT CONNECT ON DATABASE pndc TO pndc_app;
GRANT USAGE ON SCHEMA public TO pndc_app;

-- Bisagra entre los dos roles: lo que pndc_owner cree en las migraciones
-- queda accesible para pndc_app automaticamente. Sin esto, Alembic crearia
-- las tablas y la API recibiria permission denied.
ALTER DEFAULT PRIVILEGES FOR ROLE pndc_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pndc_app;

ALTER DEFAULT PRIVILEGES FOR ROLE pndc_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO pndc_app;

-- Verificacion. Se esperan dos filas de pndc_owner:
--   r  tablas      pndc_app=arwd/pndc_owner
--   S  secuencias  pndc_app=rU/pndc_owner
SELECT defaclrole::regrole AS creador,
       defaclobjtype AS tipo,
       defaclacl AS permisos
FROM pg_default_acl;
