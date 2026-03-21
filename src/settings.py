from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class GlobalConfig(BaseSettings):
    SELENE_LOG_LEVEL: LogLevel = "ERROR"
    SELENE_OLLAMA_HOST: str = "http://localhost:11434"
    SELENE_OLLAMA_MODEL: Optional[str] = None
    SELENE_TAVILY_API_KEY: Optional[str] = None

    # Setting Defaults for External Libraries
    LEANN_LOG_LEVEL: LogLevel = "WARNING"
    LEANN_SUPPRESS_OUTPUT: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_config():
    return GlobalConfig()


config = get_config()
