import sys
from pathlib import Path

import structlog
import typer
from thoughtflow import MEMORY
from typer import Exit, Option

from src.cli.chat import chat_app
from src.cli.console import echo
from src.cli.ollama import model_app
from src.cli.rag import rag_app
from src.internal.agent import selene_agent
from src.internal.memory_utils import get_memory_dir
from src.internal.prompt_utils import append_file_to_prompt
from src.logging_conf import setup_logging
from src.settings import config
from src.utils import get_version

logger = structlog.getLogger(__name__)

app = typer.Typer(help="Selene AI - Local Death Dealer Assistant")
app.add_typer(model_app, name="model")
app.add_typer(chat_app, name="chat")
app.add_typer(rag_app, name="rag")


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


@app.command("ask", help="Ask Selene a question")
def ask(
    prompt: str = typer.Argument(..., help="What to ask the model"),
    file: str = Option(None, "--file", "-f", help="Attach a file to analyze."),
) -> None:
    user_prompt = prompt
    if file:
        file_path = Path(file).expanduser().resolve()
        if not file_path.exists() or not file_path.is_file():
            echo(f"Error: file not found: {file_path}", err=True)
            raise Exit(code=1)
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            echo(f"Error reading file: {e}", err=True)
            raise Exit(code=1)
        user_prompt = append_file_to_prompt(prompt, file_path, content)

    memory = MEMORY()
    memory.add_msg(role="user", content=user_prompt, mode="text", channel="cli")
    memory = selene_agent(memory)
    echo(memory.last_asst_msg().get("content", "").lstrip())
    raise Exit(code=0)


def main():
    setup_logging()
    app()


if __name__ == "__main__":
    main()
