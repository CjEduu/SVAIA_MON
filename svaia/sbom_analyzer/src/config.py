"""
    Setting up configuration values as recommended by FASTAPI:
    https://fastapi.tiangolo.com/advanced/settings/#creating-the-settings-only-once-with-lru_cache
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name:str = "SbomAnalyserService"
    model_config = SettingsConfigDict(env_file = ".env")

