from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    pndc_env: str = "dev"
    database_url: str = "postgresql+psycopg://pndc_app:pndc_app_dev@localhost:5432/pndc"

    # Nunca se registran IPs. La bandera existe para que la ausencia sea
    # explicita y verificable en la configuracion, no solo en el codigo.
    registrar_ip: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
