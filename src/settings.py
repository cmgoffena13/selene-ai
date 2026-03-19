from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = "PROD"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class GlobalConfig(BaseConfig):
    LOG_LEVEL: LogLevel = "INFO"
    OLLAMA_MODEL: str = "mistral:7b"
    TAVILY_API_KEY: Optional[str] = None
    LEANN_LOG_LEVEL: LogLevel = "WARNING"
    LEANN_SUPPRESS_OUTPUT: bool = True


class DevConfig(GlobalConfig):
    LOG_LEVEL: LogLevel = "DEBUG"

    model_config = SettingsConfigDict(env_prefix="DEV_")


class TestConfig(GlobalConfig):
    LOG_LEVEL: LogLevel = "WARNING"

    model_config = SettingsConfigDict(env_prefix="TEST_")


class ProdConfig(GlobalConfig):
    LOG_LEVEL: LogLevel = "ERROR"

    model_config = SettingsConfigDict(env_prefix="PROD_")


@lru_cache()
def get_config(env_state: str):
    if not env_state:
        raise ValueError("ENV_STATE is not set. Possible values are: DEV, TEST, PROD")
    env_state = env_state.lower()

    configs = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
