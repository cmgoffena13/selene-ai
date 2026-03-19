import typer

from src.internal.app.chat import ChatApp

chat_app = typer.Typer(help="Open an interactive chat with Selene.")


@chat_app.callback(invoke_without_command=True)
def chat_new() -> None:
    """Open an interactive chat."""
    app = ChatApp()
    app.run()
