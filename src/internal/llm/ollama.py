from typing import Optional

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
