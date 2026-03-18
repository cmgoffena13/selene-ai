from typing import Optional

import structlog
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Static
from textual.worker import WorkerState
from thoughtflow import CHAT, MEMORY

from src.internal.agent import selene_agent

logger = structlog.getLogger(__name__)

THINKING_PHRASES = [
    "Asking the Elders…",
    "Searching the Archives…",
    "Hunting the Lycans…",
    "Loading the Silver Nitrate…",
    "Sustaining my Thirst…",
]
THINKING_INTERVAL = 2.0


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
        if text == "":
            return
        self.value = ""
        self.app.submit_user_text(text)


class ChatApp(App):
    """A Textual app to manage chats."""

    CSS_PATH = "chat_app.tcss"

    def on_mount(self) -> None:
        self.memory = MEMORY()
        self.chat = CHAT(agent=selene_agent, memory=self.memory, channel="webapp")
        self._thinking: Optional[MessageBubble] = None
        self._thinking_timer = None
        self._thinking_index = 0

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

    def _cycle_thinking_phrase(self) -> None:
        """Update the thinking bubble to the next phrase (called by timer)."""
        if self._thinking is None:
            return
        phrase = THINKING_PHRASES[self._thinking_index % len(THINKING_PHRASES)]
        self._thinking_index += 1
        self._thinking.update(phrase)

    def submit_user_text(self, text: str) -> None:
        self._append(text, "user")
        if self._thinking_timer is not None:
            self._thinking_timer.stop()
            self._thinking_timer = None
        if self._thinking is not None:
            try:
                self._thinking.remove()
            except Exception:
                pass
        self._thinking_index = 0
        self._thinking = self._append(THINKING_PHRASES[0], "thinking")
        self._thinking_timer = self.set_interval(
            THINKING_INTERVAL,
            self._cycle_thinking_phrase,
            name="thinking_phrase_cycle",
        )

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

        if self._thinking_timer is not None:
            self._thinking_timer.stop()
            self._thinking_timer = None

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
