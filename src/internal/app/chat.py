import structlog
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input
from thoughtflow import CHAT, MEMORY

from src.internal.agent import selene_agent

logger = structlog.getLogger(__name__)


class CommandPrompt(Input):
    """A text window for entering chat prompts."""

    def on_input(self, event: Input.Changed) -> None:
        """Handle the input event."""
        print(event.value)

    def on_submit(self, event: Input.Submitted) -> None:
        """Handle the submit event."""
        pass


class ChatApp(App):
    """A Textual app to manage chats."""

    CSS_PATH = "chat_app.tcss"
    memory = MEMORY()
    chat = CHAT(agent=selene_agent, memory=memory, channel="chat")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield VerticalScroll(CommandPrompt())
