import sys

from typer import Exit, Option, Typer

from src.logging_conf import set_log_level
from src.settings import config

chat_app = Typer(help="Open an interactive chat with Selene.")


@chat_app.callback(
    invoke_without_command=True, help="Open an interactive chat with Selene."
)
def chat_new(
    web: bool = Option(False, "--web", "-w", help="Serve chat UI in a web browser."),
    classic: bool = Option(
        False, "--classic", "-c", help="Use the classic Thoughtflow chat."
    ),
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Show full ThoughtFlow memory in the transcript (all roles, logs, refs, vars).",
    ),
) -> None:
    from src.internal.llm.ollama import warn_if_ollama_unreachable

    warn_if_ollama_unreachable(config.SELENE_OLLAMA_HOST)
    if web:
        set_log_level("ERROR")
        from textual_serve.server import Server

        v = "True" if verbose else "False"
        command = (
            f'{sys.executable} -c "from src.settings import config; '
            f'config.SELENE_LOG_LEVEL = \\"ERROR\\"; '
            f"from src.logging_conf import setup_logging; setup_logging(); "
            f"from src.internal.app.chat import ChatApp; "
            f'ChatApp(verbose={v}).run()"'
        )
        Server(command).serve(debug=False)
        return

    if classic:
        from thoughtflow import CHAT, MEMORY

        from src.internal.agents.orchestrator.agent import orchestrator_agent

        memory = MEMORY()
        chat = CHAT(agent=orchestrator_agent, memory=memory, channel="cli")
        chat.run()
        raise Exit(code=0)

    set_log_level("ERROR")
    from src.internal.app.chat import ChatApp

    ChatApp(verbose=verbose, watch_css=False).run()
