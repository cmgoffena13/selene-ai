from ollama import Client, RequestError, ResponseError


def is_ollama_reachable(host: str) -> bool:
    try:
        Client(host=host).list()
    except (RequestError, ResponseError, ConnectionError):
        return False
    return True


def warn_if_ollama_unreachable(host: str) -> None:
    if is_ollama_reachable(host):
        return
    from src.cli.console import echo

    echo(
        f"Warning: Ollama is not reachable at {host}. "
        "Start the server with: ollama serve, then verify this host (settings / env).",
        err=True,
    )
