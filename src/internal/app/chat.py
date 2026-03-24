import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import structlog
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.style import Style
from textual.theme import Theme
from textual.widgets import Button, Footer, Header, Select, Static, TextArea
from textual.worker import WorkerState
from thoughtflow import CHAT, MEMORY

from src.internal.agents.memory_utils import (
    delete_chat_session,
    list_chat_sessions_index,
    new_chat_session_path,
    resolve_chat_session_path,
    upsert_chat_session_index,
)
from src.internal.agents.prompt_utils import append_file_to_prompt
from src.internal.ui.theme import textual_palette
from src.settings import config

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

# Long pasted text must not be probed with stat() (ENAMETOOLONG on macOS, etc.).
_MAX_PROMPT_AS_PATH_CHARS = 4096

_URL_SPLIT = re.compile(r"(https?://\S+)")

_VERBOSE_SPEAKER_LABELS: dict[str, str] = {
    "system": "System",
    "user": "You",
    "assistant": "Selene",
    "reflection": "Reflection",
    "action": "Action",
    "query": "Query",
    "result": "Result",
    "logger": "Logger",
    "log": "Log",
    "ref": "Reflection",
    "var": "Var",
}


def _try_copy_to_system_clipboard(text: str) -> bool:
    """Use OS clipboard when available (macOS pbcopy, Wayland, X11)."""
    try:
        if p := shutil.which("pbcopy"):
            subprocess.run([p], input=text.encode("utf-8"), check=False)
            return True
        if p := shutil.which("wl-copy"):
            subprocess.run([p], input=text.encode("utf-8"), check=False)
            return True
        if p := shutil.which("xclip"):
            subprocess.run(
                [p, "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=False,
            )
            return True
    except OSError:
        pass
    return False


def _message_content_with_links(text: str) -> Content:
    """Plain text with http(s) spans styled as links (no markup string parsing)."""
    parts = _URL_SPLIT.split(text)
    merged: Content | None = None
    for part in parts:
        if not part:
            continue
        if part.startswith(("http://", "https://")):
            url = part.rstrip(".,;:!?)")
            tail = part[len(url) :]
            chunk = Content.styled(url, Style(link=url)) + Content(tail)
        else:
            chunk = Content(part)
        merged = chunk if merged is None else merged + chunk
    return merged if merged is not None else Content("")


def _link_from_click(event: events.Click, screen) -> str | None:
    """Resolve Rich link URL from the click event (web sometimes omits style on the event)."""
    link = getattr(event.style, "link", None)
    if link:
        return link
    try:
        return getattr(
            screen.get_style_at(event.screen_x, event.screen_y), "link", None
        )
    except Exception:
        return None


class BubbleBody(Static):
    """Link spans: terminal = click copies, Ctrl/⌘+click opens; web = click opens, Shift+click copies."""

    def on_click(self, event: events.Click) -> None:
        link = _link_from_click(event, self.screen)
        if not link:
            return
        event.stop()
        app = self.app
        if app.is_web:
            if event.shift:
                if not _try_copy_to_system_clipboard(link):
                    app.copy_to_clipboard(link)
            else:
                app.open_url(link)
            return
        if event.ctrl or event.meta:
            app.open_url(link)
            return
        if not _try_copy_to_system_clipboard(link):
            app.copy_to_clipboard(link)


class MessageBubble(Vertical):
    """A single chat message bubble (rounded border + inner fill)."""

    def __init__(self, text: str, *, role: str, speaker: str | None = None) -> None:
        self.role = role
        if speaker is not None:
            self.speaker = speaker
        else:
            self.speaker = (
                "Selene" if role in {"assistant", "thinking", "error"} else "You"
            )
        super().__init__()
        self._label = Static(self.speaker, classes="bubble_label")
        self._body = BubbleBody(
            _message_content_with_links(text),
            classes="bubble_body",
            markup=False,
        )
        self._content = Vertical(self._label, self._body, classes="bubble_content")
        self.add_class("bubble")
        self.add_class(role)

    def compose(self) -> ComposeResult:
        yield self._content

    def set_text(self, text: str) -> None:
        self._body.update(_message_content_with_links(text))


class MessageRow(Horizontal):
    """User bubbles left; all other roles right."""

    def __init__(
        self,
        bubble: MessageBubble,
        *,
        role: str,
        align_left: bool | None = None,
    ) -> None:
        super().__init__()
        self.bubble = bubble
        self.role = role
        if align_left is None:
            align_left = role == "user"
        self._align_left = align_left
        self.add_class("row")
        self.add_class(role)

    def compose(self) -> ComposeResult:
        spacer = Static("", classes="spacer")
        if self._align_left:
            yield self.bubble
            yield spacer
        else:
            yield spacer
            yield self.bubble


class CommandPrompt(TextArea):
    """Multiline prompt: soft-wraps to the width; Enter sends, Shift+Enter newline."""

    def __init__(
        self,
        *,
        placeholder: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            soft_wrap=True,
            compact=True,
            tab_behavior="focus",
            show_line_numbers=False,
            highlight_cursor_line=False,
        )

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        assert isinstance(self.app, ChatApp)
        if self.app.maybe_attach_file_from_input(self.text):
            self.text = ""

    async def _on_key(self, event: events.Key) -> None:
        if event.key in ("enter", "ctrl+m"):
            event.prevent_default()
            event.stop()
            text = self.text.strip()
            if text == "":
                return
            self.text = ""
            assert isinstance(self.app, ChatApp)
            self.app.submit_user_text(text)
            return
        await super()._on_key(event)


class ChatApp(App):
    TITLE = "Interactive Chat"
    CSS_PATH = "chat_app.tcss"

    def __init__(
        self,
        verbose: bool = False,
        *,
        driver_class=None,
        css_path=None,
        watch_css: bool = False,
        ansi_color: bool = False,
    ) -> None:
        super().__init__(
            driver_class=driver_class,
            css_path=css_path,
            watch_css=watch_css,
            ansi_color=ansi_color,
        )
        self._verbose = verbose

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
        self.chat = CHAT(
            agent=config.SELENE_AGENT, memory=self.memory, channel="webapp"
        )
        self._current_session_path: Path = new_chat_session_path()
        self._attached_file_path: Optional[Path] = None
        self._thinking: Optional[MessageBubble] = None
        self._refresh_session_dropdown()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="chat_root"):
            with Horizontal(id="session_controls"):
                yield Select([], prompt="Sessions", id="session_select")
                yield Button("New", id="new_session")
                yield Button("Delete", id="delete_session")
            yield VerticalScroll(id="transcript")
            with Horizontal(id="prompt_row"):
                yield CommandPrompt(placeholder="Ask Selene…", id="prompt")
                yield Static("", id="attach_icon")
        yield Footer()

    def _append(
        self,
        text: str,
        role: str,
        *,
        speaker: str | None = None,
        align_left: bool | None = None,
    ) -> MessageBubble:
        transcript = self.query_one("#transcript", VerticalScroll)
        bubble = MessageBubble(text, role=role, speaker=speaker)
        transcript.mount(MessageRow(bubble, role=role, align_left=align_left))
        transcript.scroll_end(animate=False)
        return bubble

    def _append_memory_event(self, ev: dict) -> None:
        """Render one MEMORY event for verbose transcript."""
        t = ev["type"]
        if t == "msg":
            role: str = ev["role"]
            content = str(ev["content"])
            if role == "user":
                self._append(content, "user")
            elif role == "assistant":
                self._append(content, "assistant")
            else:
                self._append(content, "verbose", speaker=_VERBOSE_SPEAKER_LABELS[role])
        elif t in ("log", "ref", "var"):
            self._append(
                str(ev["content"]), "verbose", speaker=_VERBOSE_SPEAKER_LABELS[t]
            )

    def _rebuild_transcript_verbose(self) -> None:
        for ev in self.chat.memory.get_events():
            self._append_memory_event(ev)

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
        s = raw.strip().strip("'\"")
        if not s or len(s) > _MAX_PROMPT_AS_PATH_CHARS:
            return None
        if s.startswith("file://"):
            s = unquote(urlparse(s).path)
        p = Path(s).expanduser()
        try:
            if p.is_file():
                return p.resolve()
        except OSError:
            return None
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
            self._thinking.remove()
        phrase = THINKING_PHRASES[random.randrange(len(THINKING_PHRASES))]
        self._thinking = self._append(phrase, "thinking")

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
        prompt.text = ""
        self._refresh_session_dropdown()

    def _rebuild_transcript_from_memory(self) -> None:
        self._clear_transcript()
        self._thinking = None
        if self._verbose:
            self._rebuild_transcript_verbose()
            return
        for msg in self.chat.memory.get_msgs(include=["user", "assistant"]):
            role = msg.get("role")
            content = msg["content"]
            if role in {"user", "assistant"}:
                self._append(content, role)

    def _autosave_current_session(self) -> None:
        self.chat.memory.to_json(str(self._current_session_path))
        first_user = self.chat.memory.get_msgs(include=["user"])[0]["content"]
        upsert_chat_session_index(self._current_session_path.name, first_user)
        self._refresh_session_dropdown()

    def _load_session_file(self, filename: str) -> None:
        load_path = resolve_chat_session_path(filename)
        if not load_path.exists():
            raise ValueError(f"Session file not found: {load_path}")
        self.workers.cancel_group(self, "agent")
        loaded = MEMORY.from_json(str(load_path))
        self.memory = loaded
        self.chat.memory = self.memory
        self._current_session_path = load_path
        self._rebuild_transcript_from_memory()
        self.query_one("#transcript", VerticalScroll).scroll_end(animate=False)
        self._refresh_session_dropdown()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "session_select":
            return
        if event.value is Select.NULL:
            return
        filename = str(event.value)
        if filename == self._current_session_path.name:
            return
        self._load_session_file(filename)

    def _refresh_session_dropdown(self) -> None:
        select = self.query_one("#session_select", Select)
        sessions = list_chat_sessions_index()
        options = []
        for session in sessions:
            filename = session["filename"]
            display_name = Path(filename).stem
            first_prompt = session["first_prompt"]
            if len(first_prompt) > FIRST_PROMPT_PREVIEW_LEN:
                prompt_preview = f"{first_prompt[:FIRST_PROMPT_PREVIEW_LEN]}..."
            else:
                prompt_preview = first_prompt
            label = f'{display_name} - "{prompt_preview}"'
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

    def on_worker_state_changed(self, event) -> None:
        worker = event.worker
        if getattr(worker, "name") != "agent_turn":
            return

        if worker.state == WorkerState.SUCCESS:
            if self._verbose:
                if self._thinking is not None:
                    self._thinking.remove()
                    self._thinking = None
                self._rebuild_transcript_from_memory()
            else:
                response = worker.result.lstrip()
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
            if self._verbose:
                if self._thinking is not None:
                    self._thinking.remove()
                    self._thinking = None
                self._rebuild_transcript_from_memory()
                self._append(msg, "error")
            elif self._thinking is not None:
                self._thinking.set_text(msg)
                self._thinking.remove_class("thinking")
                self._thinking.add_class("error")
                self._thinking = None
            else:
                self._append(msg, "error")
            self.query_one("#transcript", VerticalScroll).scroll_end(animate=True)
            self._autosave_current_session()
