import sys
from pathlib import Path

import structlog
from thoughtflow import MEMORY
from typer import Argument, Exit, Option, Typer

from src.cli.chat import chat_app
from src.cli.ollama import model_app
from src.cli.rag import rag_app
from src.internal.agents.prompt_utils import append_file_to_prompt
from src.internal.llm.ollama import warn_if_ollama_unreachable
from src.logging_conf import setup_logging
from src.settings import config
from src.utils import get_selene_ai_config_dir, get_version

logger = structlog.getLogger("src.cli.selene")

app = Typer(help="Selene AI - Death Dealer, Elder Slayer, Silent Watcher")
app.add_typer(model_app, name="model")
app.add_typer(chat_app, name="chat")
app.add_typer(rag_app, name="rag")


@app.callback(no_args_is_help=True, invoke_without_command=True)
def main_menu(
    version: bool = Option(False, "--version", help="Show CLI version and exit"),
    info: bool = Option(False, "--info", help="Show general CLI info and exit"),
) -> None:
    from src.internal.ui.console import echo

    if version:
        echo(f"Selene AI - Version: {get_version()}")
        raise Exit(code=0)
    if info:
        cli_path = Path(sys.argv[0]).resolve()
        echo(f"CLI Path: {cli_path}")
        echo(f"Config Directory: {get_selene_ai_config_dir()}/")
        echo(f"Ollama Model: {config.SELENE_OLLAMA_MODEL}")
        raise Exit(code=0)


@app.command("ask", help="Ask Selene a question")
def ask(
    prompt: str = Argument(..., help="What to ask the model"),
    file: str = Option(None, "--file", "-f", help="Attach a file to analyze."),
    verbose: bool = Option(False, "--verbose", "-v", help="Show verbose output."),
) -> None:
    from src.internal.agents.router.agent import router_agent
    from src.internal.ui.console import echo

    warn_if_ollama_unreachable(config.SELENE_OLLAMA_HOST)
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
    logger.info("Asking Selene a question", user_prompt=user_prompt)
    memory = router_agent(memory)
    if verbose:
        echo(memory.render())
    else:
        echo(memory.last_asst_msg()["content"].lstrip())
    raise Exit(code=0)


def main():
    setup_logging()
    app()


if __name__ == "__main__":
    main()
