import sys

import typer
from typer import Option

from src.internal.app.chat import ChatApp

chat_app = typer.Typer(help="Open an interactive chat with Selene.")


@chat_app.callback(invoke_without_command=True)
def chat_new(
    web: bool = Option(False, "--web", "-w", help="Serve chat UI in a web browser."),
) -> None:
    """Open an interactive chat with Selene."""
    if web:
        from textual_serve.server import Server

        command = f'{sys.executable} -c "from src.internal.app.chat import ChatApp; ChatApp().run()"'
        Server(command).serve(debug=False)
        return

    app = ChatApp(watch_css=True)
    app.run()
