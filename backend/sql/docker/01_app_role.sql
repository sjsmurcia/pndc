/*
se ejectua automaticamente al inicializar el contenedor de postgresql
la base y el rol propietario ya los crea la imagen a partir de 
POSTGRES_DB y POSTGRES_USER, falta el rol de la aplicacion

*/

CREATE ROLE pndc_app LOGIN PASSWORD 'pndc_app_dev';

GRANT CONNECT ON DATABASE pndc TO pndc_app;
GRANT USAGE ON SCHEMA public TO pndc_app;

ALTER DEFAULT PRIVILEGES FOR ROLE pndc_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pndc_app;

ALTER DEFAULT PRIVILEGES FOR ROLE pndc_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO pndc_app;

