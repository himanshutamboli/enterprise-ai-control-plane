"""Application settings, sourced from environment (prefix ``CONTROL_PLANE_``) or a .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONTROL_PLANE_", env_file=".env", extra="ignore")

    app_name: str = "Enterprise AI Control Plane"
    environment: str = "development"
    # sqlite by default so it runs with zero infra; point at Postgres in production.
    database_url: str = "sqlite:///./data/control_plane.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
