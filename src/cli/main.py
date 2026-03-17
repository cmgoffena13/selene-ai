import sys
from pathlib import Path

import structlog
import typer
from thoughtflow import MEMORY
from typer import Exit, Option, echo

from src.cli.ollama import model_app
from src.internal.agent import selene_agent
from src.internal.memory_utils import get_memory_dir
from src.logging_conf import setup_logging
from src.settings import config
from src.utils import get_version

logger = structlog.getLogger(__name__)

app = typer.Typer(help="Selene AI - Local Death Dealer Assistant")
app.add_typer(model_app, name="model")


@app.callback(no_args_is_help=True, invoke_without_command=True)
def main_menu(
    version: bool = Option(False, "--version", help="Show CLI version and exit"),
    info: bool = Option(False, "--info", help="Show general CLI info and exit"),
) -> None:
    if version:
        echo(f"Selene AI - Version: {get_version()}")
        raise Exit(code=0)
    if info:
        cli_path = Path(sys.argv[0]).resolve()
        echo(f"CLI Path: {cli_path}")
        echo(f"Memory directory: {get_memory_dir()}")
        echo(f"Ollama model: {config.OLLAMA_MODEL}")
        raise Exit(code=0)


@app.command("ask")
def ask(
    prompt: str = typer.Argument(..., help="What to ask the model"),
) -> None:
    memory = MEMORY()
    memory.add_msg(role="user", content=prompt, mode="text", channel="cli")
    memory = selene_agent(memory)
    echo(memory.render())
    raise Exit(code=0)


# Top-level subcommands;
_KNOWN_COMMANDS = ("model", "ask")


def main():
    setup_logging()

    # NOTE: Cobra-style: selene "prompt" or selene word word → selene ask "<prompt>"
    if len(sys.argv) >= 2:
        first = sys.argv[1]
        if not first.startswith("-") and first not in _KNOWN_COMMANDS:
            sys.argv = [sys.argv[0], "ask", " ".join(sys.argv[1:])]

    app()


if __name__ == "__main__":
    main()
