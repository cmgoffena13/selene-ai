import typer
from ollama import Client, RequestError, ResponseError
from typer import Exit, Option, echo

model_app = typer.Typer(help="Manage Ollama models (pull, list).")


@model_app.command("list")
def model_list(
    host: str = Option("http://localhost:11434", "--host", "-H", help="Ollama host"),
) -> None:
    """List Ollama models available locally."""
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
        size = f"  {m.size}" if getattr(m, "size", None) else ""
        echo(f"  {name}{size}")


@model_app.command("pull")
def model_pull(
    name: str = typer.Argument(..., help="Model name (e.g. llama3.2, mistral)"),
    host: str = Option("http://localhost:11434", "--host", "-H", help="Ollama host"),
) -> None:
    """Pull an Ollama model so you can use it with Selene."""
    try:
        client = Client(host=host)
        echo(f"Pulling {name}...")
        resp = client.pull(name, stream=False)
        echo(f"Done. {resp.status or 'Ready'}.")
    except (RequestError, ResponseError) as e:
        echo(f"Ollama error: {e}", err=True)
        echo("Is Ollama running? Start it with: ollama serve", err=True)
        raise Exit(code=1)
