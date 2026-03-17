import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer
from rich.logging import RichHandler
from typer import Exit, Option, echo

from src.cli.ollama import model_app
from src.internal.llm.ollama import get_ollama_llm
from src.internal.memory_utils import get_memory_dir
from src.logging_conf import setup_logging
from src.settings import config
from src.utils import get_version

logger = structlog.getLogger(__name__)

app = typer.Typer(help="Selene AI - Local AI Assistant")
app.add_typer(model_app, name="model")


@app.callback(no_args_is_help=True, invoke_without_command=True)
def main_menu(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Argument(
        None,
        help='Ask something: selene "Who won the war in Underworld? Vampires or werewolves?"',
    ),
    version: bool = Option(False, "--version", help="Show CLI version and exit"),
    info: bool = Option(False, "--info", help="Show general CLI info and exit"),
) -> None:
    llm = get_ollama_llm(config.OLLAMA_MODEL)
    ctx.obj = {"llm": llm}
    if version:
        echo(f"Selene AI - Version: {get_version()}")
        raise Exit(code=0)
    if info:
        cli_path = Path(sys.argv[0]).resolve()
        echo(f"CLI Path: {cli_path}")
        echo(f"Memory directory: {get_memory_dir()}")
        echo(f"Ollama model: {config.OLLAMA_MODEL}")
        raise Exit(code=0)
    if prompt is not None:
        choices = llm.call([{"role": "user", "content": prompt}], {})
        if choices:
            echo(choices[0])
        raise Exit(code=0)


def main():
    setup_logging()
    root_logger = logging.getLogger("src")
    for handler in root_logger.handlers:
        if isinstance(handler, RichHandler):
            # handler.console = console
            handler.show_time = False
            handler.show_path = False
            handler.highlighter = None
    app()


if __name__ == "__main__":
    main()
