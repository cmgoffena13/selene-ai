from typing import Optional

from ollama import Client, RequestError, ResponseError
from thoughtflow import LLM


def get_ollama_llm(model: Optional[str]) -> LLM:
    """
    Return a thoughtflow LLM that uses Ollama at http://localhost:11434 (default).

    Use with MEMORY, THOUGHT, AGENT, etc. For a different host, pass
    ollama_url in the step's params when calling.
    """

    if model is None:
        raise ValueError("Ollama model is not set")
    return LLM(f"ollama:{model}", key="")


def is_ollama_reachable(host: str) -> bool:
    try:
        Client(host=host).list()
    except (RequestError, ResponseError, ConnectionError):
        return False
    return True


def warn_if_ollama_unreachable(host: str) -> None:
    if is_ollama_reachable(host):
        return
    from src.internal.ui.console import echo

    echo(
        f"Warning: Ollama is not reachable at {host}. "
        "Start the server with: ollama serve, then verify this host (settings / env).",
        err=True,
    )
