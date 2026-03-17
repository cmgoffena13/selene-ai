from thoughtflow import LLM


def get_ollama_llm(model: str) -> LLM:
    """
    Return a thoughtflow LLM that uses Ollama at http://localhost:11434.

    Use with MEMORY, THOUGHT, AGENT, etc. For a different host, pass
    ollama_url in the step's params when calling.
    """
    return LLM(f"ollama:{model}", key="")
