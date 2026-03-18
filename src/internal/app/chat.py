import structlog
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Static
from textual.worker import WorkerState
from thoughtflow import CHAT, MEMORY

from src.internal.agent import selene_agent

logger = structlog.getLogger(__name__)


class MessageBubble(Static):
    """A single chat message bubble."""

    def __init__(self, text: str, *, role: str) -> None:
        super().__init__(text)
        self.add_class("bubble")
        self.add_class(role)


class CommandPrompt(Input):
    """A text window for entering chat prompts."""

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the submit event (Enter key)."""
        text = (event.value or "").strip()
        if not text and text != "":
            return
        self.value = ""
        self.app.submit_user_text(text)


class ChatApp(App):
    """A Textual app to manage chats."""

    CSS_PATH = "chat_app.tcss"

    def on_mount(self) -> None:
        self.memory = MEMORY()
        self.chat = CHAT(agent=selene_agent, memory=self.memory, channel="webapp")
        self._thinking: MessageBubble | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="chat_root"):
            yield VerticalScroll(id="transcript")
            yield CommandPrompt(placeholder="Ask Selene…", id="prompt")
        yield Footer()

    def _append(self, text: str, role: str) -> MessageBubble:
        transcript = self.query_one("#transcript", VerticalScroll)
        bubble = MessageBubble(text, role=role)
        transcript.mount(bubble)
        transcript.scroll_end(animate=False)
        return bubble

    def submit_user_text(self, text: str) -> None:
        self._append(text, "user")
        if self._thinking is not None:
            try:
                self._thinking.remove()
            except Exception:
                pass
        self._thinking = self._append("…", "thinking")

        self.run_worker(
            lambda: self.chat.turn(text),
            name="agent_turn",
            group="agent",
            exclusive=True,
            thread=True,
            exit_on_error=False,
        )

    def on_worker_state_changed(self, event) -> None:
        worker = event.worker
        if getattr(worker, "name", "") != "agent_turn":
            return

        if worker.state == WorkerState.SUCCESS:
            response = worker.result or "(no response)"
            if self._thinking is not None:
                self._thinking.update(response)
                self._thinking.remove_class("thinking")
                self._thinking.add_class("assistant")
                self._thinking = None
            else:
                self._append(response, "assistant")
            return

        if worker.state in {WorkerState.ERROR, WorkerState.CANCELLED}:
            msg = (
                f"Error: {worker.error!r}"
                if worker.state == WorkerState.ERROR
                else "Cancelled."
            )
            if self._thinking is not None:
                self._thinking.update(msg)
                self._thinking.remove_class("thinking")
                self._thinking.add_class("error")
                self._thinking = None
            else:
                self._append(msg, "error")
