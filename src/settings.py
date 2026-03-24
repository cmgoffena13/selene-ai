from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from thoughtflow import AGENT

from src.internal.agents.general.agent import selene_agent
from src.internal.agents.planact.agent import planact_agent
from src.internal.agents.react.agent import react_agent
from src.internal.agents.reflect.agent import reflect_agent

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _env_file_paths() -> tuple[str, ...]:
    paths: list[str] = []
    repo_root = Path(__file__).resolve().parent.parent
    # Local for Development
    if (repo_root / "pyproject.toml").is_file():
        paths.append(str(repo_root / ".env"))
    # Global for Production
    paths.append(str(Path.home() / ".config" / "selene_ai" / ".env"))
    return tuple(paths)


class GlobalConfig(BaseSettings):
    SELENE_LOG_LEVEL: LogLevel = "ERROR"
    SELENE_OLLAMA_HOST: str = "http://localhost:11434"
    SELENE_OLLAMA_MODEL: Optional[str] = None
    SELENE_OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    SELENE_TAVILY_API_KEY: Optional[str] = None
    SELENE_AGENT: AGENT = planact_agent

    # Setting Defaults for External Libraries
    LEANN_LOG_LEVEL: LogLevel = "WARNING"
    LEANN_SUPPRESS_OUTPUT: bool = True

    model_config = SettingsConfigDict(env_file=_env_file_paths(), extra="ignore")


@lru_cache()
def get_config():
    return GlobalConfig()


config = get_config()
