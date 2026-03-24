import sys

from typer import Option, Typer

chat_app = Typer(help="Open an interactive chat with Selene.")


@chat_app.callback(
    invoke_without_command=True, help="Open an interactive chat with Selene."
)
def chat_new(
    web: bool = Option(False, "--web", "-w", help="Serve chat UI in a web browser."),
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Show full ThoughtFlow memory in the transcript (all roles, logs, refs, vars).",
    ),
) -> None:
    if web:
        from textual_serve.server import Server

        v = "True" if verbose else "False"
        command = (
            f'{sys.executable} -c "from src.internal.app.chat import ChatApp; '
            f'ChatApp(verbose={v}).run()"'
        )
        Server(command).serve(debug=False)
        return

    from src.internal.app.chat import ChatApp

    ChatApp(verbose=verbose, watch_css=False).run()
