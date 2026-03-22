from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import structlog
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.theme import Theme
from textual.widgets import Button, Footer, Header, Input, Select, Static
from textual.worker import WorkerState
from thoughtflow import CHAT, MEMORY

from src.internal.agents.general.agent import selene_agent
from src.internal.agents.memory_utils import (
    delete_chat_session,
    list_chat_sessions_index,
    new_chat_session_path,
    resolve_chat_session_path,
    upsert_chat_session_index,
)
from src.internal.agents.prompt_utils import append_file_to_prompt
from src.internal.ui.theme import textual_palette

logger = structlog.getLogger(__name__)

THINKING_PHRASES = [
    "Asking the Elders…",
    "Searching the Archives…",
    "Hunting the Lycans…",
    "Feeding my Hunger…",
    "Protecting the Coven…",
    "Withholding my Judgement…",
    "Honoring the Bloodlines…",
    "Seeking the Truth…",
]

FIRST_PROMPT_PREVIEW_LEN = 50


class MessageBubble(Vertical):
    """A single chat message bubble (rounded border + inner fill)."""

    def __init__(self, text: str, *, role: str) -> None:
        self.role = role
        self.speaker = "Selene" if role in {"assistant", "thinking", "error"} else "You"
        super().__init__()
        self._label = Static(self.speaker, classes="bubble_label")
        self._body = Static(text, classes="bubble_body")
        self._content = Vertical(self._label, self._body, classes="bubble_content")
        self.add_class("bubble")
        self.add_class(role)

    def compose(self) -> ComposeResult:
        yield self._content

    def set_text(self, text: str) -> None:
        self._body.update(text)


class MessageRow(Horizontal):
    """A row that aligns user left / assistant right."""

    def __init__(self, bubble: MessageBubble, *, role: str) -> None:
        super().__init__()
        self.bubble = bubble
        self.role = role
        self.add_class("row")
        self.add_class(role)

    def compose(self) -> ComposeResult:
        spacer = Static("", classes="spacer")
        if self.role == "user":
            yield self.bubble
            yield spacer
        else:
            yield spacer
            yield self.bubble


class CommandPrompt(Input):
    """A text window for entering chat prompts."""

    def on_input_changed(self, event: Input.Changed) -> None:
        """Detect dropped/pasted file path and attach it."""

        assert isinstance(self.app, ChatApp)
        if self.app.maybe_attach_file_from_input(event.value):
            self.value = ""

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the submit event (Enter key)."""
        text = (event.value or "").strip()
        if text == "":
            return
        self.value = ""

        assert isinstance(self.app, ChatApp)
        self.app.submit_user_text(text)


class ChatApp(App):
    TITLE = "Interactive Chat"
    CSS_PATH = "chat_app.tcss"

    def on_mount(self) -> None:
        palette = textual_palette(getattr(self.console, "color_system", None))
        app_theme = Theme(
            name="selene-dark",
            primary=palette["main"],
            secondary=palette["panel"],
            accent=palette["border"],
            foreground=palette["main"],
            background=palette["background"],
            surface=palette["surface"],
            panel=palette["panel"],
            dark=True,
        )
        self.register_theme(app_theme)
        self.theme = app_theme.name

        self.memory = MEMORY()
        self.chat = CHAT(agent=selene_agent, memory=self.memory, channel="webapp")
        self._current_session_path: Path = new_chat_session_path()
        self._attached_file_path: Optional[Path] = None
        self._thinking: Optional[MessageBubble] = None
        self._thinking_index = -1
        self._refresh_session_dropdown()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="chat_root"):
            with Horizontal(id="session_controls"):
                yield Select([], prompt="Sessions", id="session_select")
                yield Button("New", id="new_session")
                yield Button("Load", id="load_session")
                yield Button("Delete", id="delete_session")
            yield VerticalScroll(id="transcript")
            with Horizontal(id="prompt_row"):
                yield CommandPrompt(placeholder="Ask Selene…", id="prompt")
                yield Static("", id="attach_icon")
        yield Footer()

    def _append(self, text: str, role: str) -> MessageBubble:
        transcript = self.query_one("#transcript", VerticalScroll)
        bubble = MessageBubble(text, role=role)
        transcript.mount(MessageRow(bubble, role=role))
        transcript.scroll_end(animate=False)
        return bubble

    def _update_prompt_placeholder(self) -> None:
        prompt = self.query_one("#prompt", CommandPrompt)
        attach_icon = self.query_one("#attach_icon", Static)
        if self._attached_file_path is None:
            prompt.placeholder = "Ask Selene…"
            attach_icon.update("")
        else:
            prompt.placeholder = (
                f'Attached "{self._attached_file_path.name}". Ask Selene…'
            )
            attach_icon.update("📄")

    def _extract_file_path(self, raw: str) -> Optional[Path]:
        text = (raw or "").strip()
        if not text:
            return None
        if (text.startswith('"') and text.endswith('"')) or (
            text.startswith("'") and text.endswith("'")
        ):
            text = text[1:-1]
        if text.startswith("file://"):
            parsed = urlparse(text)
            text = unquote(parsed.path or "")
        path = Path(text).expanduser()
        if path.exists() and path.is_file():
            return path.resolve()
        return None

    def maybe_attach_file_from_input(self, raw: str) -> bool:
        path = self._extract_file_path(raw)
        if path is None:
            return False
        self._attached_file_path = path
        self._update_prompt_placeholder()
        return True

    def submit_user_text(self, text: str) -> None:
        model_prompt = text
        if self._attached_file_path is not None:
            try:
                content = self._attached_file_path.read_text(
                    encoding="utf-8", errors="replace"
                )
            except Exception as e:
                self._append(f"Attachment read error: {e}", "error")
                self._attached_file_path = None
                self._update_prompt_placeholder()
                return
            model_prompt = append_file_to_prompt(
                text, self._attached_file_path, content
            )
            self._attached_file_path = None
            self._update_prompt_placeholder()

        self._append(text, "user")
        if self._thinking is not None:
            try:
                self._thinking.remove()
            except Exception:
                pass
        self._thinking_index = (self._thinking_index + 1) % len(THINKING_PHRASES)
        self._thinking = self._append(
            THINKING_PHRASES[self._thinking_index], "thinking"
        )

        self.run_worker(
            lambda: self.chat.turn(model_prompt),
            name="agent_turn",
            group="agent",
            exclusive=True,
            thread=True,
            exit_on_error=False,
        )

    def _clear_transcript(self) -> None:
        transcript = self.query_one("#transcript", VerticalScroll)
        transcript.remove_children()

    def _reset_to_new_session(self) -> None:
        self.memory = MEMORY()
        self.chat.memory = self.memory
        self._current_session_path = new_chat_session_path()
        self._thinking = None
        self._attached_file_path = None
        self._update_prompt_placeholder()
        self._clear_transcript()
        prompt = self.query_one("#prompt", CommandPrompt)
        prompt.value = ""
        self._refresh_session_dropdown()

    def _rebuild_transcript_from_memory(self) -> None:
        self._clear_transcript()
        self._thinking = None
        for msg in self.chat.memory.get_msgs(include=["user", "assistant"]):
            role = msg.get("role")
            content = msg.get("content", "")
            if role in {"user", "assistant"}:
                self._append(content, role)

    def _autosave_current_session(self) -> None:
        self.chat.memory.to_json(str(self._current_session_path))
        first_user = self.chat.memory.last_user_msg(content_only=True)
        upsert_chat_session_index(self._current_session_path.name, first_user)
        self._refresh_session_dropdown()

    def _refresh_session_dropdown(self) -> None:
        select = self.query_one("#session_select", Select)
        sessions = list_chat_sessions_index()
        options = []
        for session in sessions:
            filename = session["filename"]
            display_name = Path(filename).stem
            first_prompt = (session.get("first_prompt") or "").strip()
            if len(first_prompt) > FIRST_PROMPT_PREVIEW_LEN:
                prompt_preview = f"{first_prompt[:FIRST_PROMPT_PREVIEW_LEN]}..."
            else:
                prompt_preview = first_prompt
            label = (
                f'{display_name} - "{prompt_preview}"'
                if prompt_preview
                else display_name
            )
            options.append((label, filename))
        select.set_options(options)
        if sessions:
            current_name = self._current_session_path.name
            available_names = {session["filename"] for session in sessions}
            if current_name in available_names:
                select.value = current_name
            else:
                # New / unsaved session (e.g. before first turn autosave): show prompt only.
                select.clear()
        else:
            select.clear()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        selected = self.query_one("#session_select", Select).value

        if button_id == "new_session":
            self.workers.cancel_group(self, "agent")
            self._reset_to_new_session()
            return

        if button_id == "delete_session":
            if not selected:
                return
            filename = str(selected)
            deleting_current = self._current_session_path.name == filename
            delete_chat_session(filename)
            if deleting_current:
                self.workers.cancel_group(self, "agent")
                self._reset_to_new_session()
            else:
                self._refresh_session_dropdown()
            return

        if button_id == "load_session":
            if not selected:
                return
            load_path = resolve_chat_session_path(str(selected))
            if not load_path.exists():
                return

            loaded = MEMORY.from_json(str(load_path))
            self.memory = loaded
            self.chat.memory = self.memory
            self._current_session_path = load_path
            self._rebuild_transcript_from_memory()
            self.query_one("#transcript", VerticalScroll).scroll_end(animate=False)
            self._refresh_session_dropdown()
            return

    def on_worker_state_changed(self, event) -> None:
        worker = event.worker
        if getattr(worker, "name", "") != "agent_turn":
            return

        if worker.state == WorkerState.SUCCESS:
            response = (worker.result or "(no response)").lstrip()
            if self._thinking is not None:
                self._thinking.set_text(response)
                self._thinking.remove_class("thinking")
                self._thinking.add_class("assistant")
                self._thinking = None
            else:
                self._append(response, "assistant")
            self.query_one("#transcript", VerticalScroll).scroll_end(animate=True)
            self._autosave_current_session()
            return

        if worker.state in {WorkerState.ERROR, WorkerState.CANCELLED}:
            msg = (
                f"Error: {worker.error!r}"
                if worker.state == WorkerState.ERROR
                else "Cancelled."
            )
            if self._thinking is not None:
                self._thinking.set_text(msg)
                self._thinking.remove_class("thinking")
                self._thinking.add_class("error")
                self._thinking = None
            else:
                self._append(msg, "error")
            self.query_one("#transcript", VerticalScroll).scroll_end(animate=True)
            self._autosave_current_session()
