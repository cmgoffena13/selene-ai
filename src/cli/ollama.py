from ollama import Client, RequestError, ResponseError
from typer import Argument, Exit, Option, Typer

from src.settings import config

model_app = Typer(help="Manage Ollama models (pull, list, remove).")


@model_app.command("list")
def model_list(
    host: str = Option(config.OLLAMA_HOST, "--host", "-H", help="Ollama host"),
) -> None:
    """List Ollama models available locally."""

    from src.cli.console import echo

    try:
        client = Client(host=host)
        resp = client.list()
    except (RequestError, ResponseError) as e:
        echo(f"Ollama error: {e}", err=True)
        echo("Is Ollama running? Start it with: ollama serve", err=True)
        raise Exit(code=1)
    if not resp.models:
        echo("No models installed. Pull one with: selene model pull <name>")
        return
    for m in resp.models:
        name = m.model or "(no name)"
        size_bytes = getattr(m, "size", None)
        size_display = (
            f"  {size_bytes / (1024**3):.1f} GB" if size_bytes is not None else ""
        )
        echo(f"  {name}{size_display}")


@model_app.command("pull")
def model_pull(
    name: str = Argument(..., help="Model name (e.g. llama3.2, mistral)"),
    host: str = Option(config.OLLAMA_HOST, "--host", "-H", help="Ollama host"),
) -> None:
    """Pull an Ollama model so you can use it with Selene."""

    from src.cli.console import echo

    try:
        client = Client(host=host)
        echo(f"Pulling {name}...")
        stream = client.pull(name, stream=True)
        last_status = ""

        for chunk in stream:
            status = getattr(chunk, "status", None)
            completed = getattr(chunk, "completed", None)
            total = getattr(chunk, "total", None)

            if isinstance(chunk, dict):
                status = chunk.get("status", status)
                completed = chunk.get("completed", completed)
                total = chunk.get("total", total)

            if status and status != last_status:
                if (
                    isinstance(completed, (int, float))
                    and isinstance(total, (int, float))
                    and total > 0
                ):
                    pct = (completed / total) * 100
                    echo(f"{status} ({pct:.0f}%)")
                else:
                    echo(status)
                last_status = status

        echo(f"Done. {last_status or 'Ready'}.")
    except (RequestError, ResponseError) as e:
        echo(f"Ollama error: {e}", err=True)
        echo("Is Ollama running? Start it with: ollama serve", err=True)
        raise Exit(code=1)


@model_app.command("delete")
def model_remove(
    name: str = Argument(..., help="Model name to remove (e.g. llama3.2)"),
    host: str = Option(config.OLLAMA_HOST, "--host", "-H", help="Ollama host"),
) -> None:
    from src.cli.console import echo

    """Remove a local Ollama model."""
    try:
        client = Client(host=host)
        echo(f"Removing {name}...")
        resp = client.delete(name)
        echo(f"Done. {resp.status or 'Removed'}.")
    except (RequestError, ResponseError) as e:
        echo(f"Ollama error: {e}", err=True)
        echo("Is Ollama running? Start it with: ollama serve", err=True)
        raise Exit(code=1)
