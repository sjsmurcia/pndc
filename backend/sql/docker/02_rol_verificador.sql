--ROL del verificador independiente

--SOLO SELECT SOBRE LA TABLA DE BITACORAS
CREATE ROLE pndc_verificador LOGIN PASSWORD 'pndc_verif_dev';

GRANT CONNECT ON DATABASE pndc TO pndc_verificador;
GRANT USAGE ON SCHEMA public TO pndc_verificador;

ALTER DEFAULT PRIVILEGES FOR ROLE pndc_owner IN SCHEMA public
    GRANT SELECT ON TABLES TO pndc_verificador;