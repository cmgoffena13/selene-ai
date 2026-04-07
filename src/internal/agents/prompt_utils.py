import datetime
import json
from pathlib import Path
from typing import Any


def extract_tool_result_payload(memory: Any) -> str | None:
    """
    Inner tool output string from the last ``result`` message.

    ThoughtFlow stores tool results as JSON:
    ``{"name": "<tool>", "result": "<tool return string>"}``.
    When the model only calls tools (no assistant message), validation must read
    this, not ``last_asst_msg``.
    """
    msgs = memory.get_msgs(include=["result"])
    if not msgs:
        return None
    raw = msgs[-1].get("content", "") or ""
    if not raw.strip():
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    inner = obj.get("result")
    if inner is None:
        return None
    return str(inner).lstrip()


def agents_root() -> Path:
    """Directory containing per-agent packages (each with ``prompt.md``)."""
    return Path(__file__).resolve().parent


def load_agent_prompt(agent_name: str) -> str:
    """Load the agent prompt for the given agent name."""
    path = agents_root() / agent_name / "prompt.md"
    if not path.is_file():
        raise FileNotFoundError(f"Missing agent prompt: {path}")
    system_prompt = path.read_text(encoding="utf-8")
    return inject_system_prompt_placeholders(system_prompt)


def ensure_agent_prompt_file(agent_name: str, *, template: str | None = None) -> Path:
    """
    Ensure ``<agent_name>/prompt.md`` exists; create parent dirs and a stub if not.

    Returns the path to ``prompt.md``.
    """
    path = agents_root() / agent_name / "prompt.md"
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    body = template if template is not None else f"# {agent_name}\n\n"
    path.write_text(body, encoding="utf-8")
    return path


def apply_planner_agent_hint(system_prompt: str, agent_hint: str | None) -> str:
    """
    Append planner ``agent_hint`` to a sub-agent system prompt when present.

    Keeps specialist prompts unchanged when routing provides no hint.
    """
    if agent_hint is None or not str(agent_hint).strip():
        return system_prompt
    return (
        f"{system_prompt.rstrip()}\n\n## Planner Guidance\n{str(agent_hint).strip()}\n"
    )


def inject_system_prompt_placeholders(template: str) -> str:
    """
    Replace placeholders in the system prompt template (e.g. {current_date}).

    The date is computed when this runs (typically at process / agent init).
    Uses string replace instead of str.format so literals like ``{}`` or
    ``{{task}}`` in prompts are not interpreted as format fields.
    """
    current_date = datetime.datetime.today().strftime("%A, %B %d, %Y")
    return template.replace(f"{{current_date}}", current_date)


def format_file_attachment(filename: str, content: str) -> str:
    """Format one file attachment block for prompt context."""
    return (
        f"Filename: {filename}\n"
        "File contents:\n"
        "----- BEGIN FILE CONTENTS -----\n"
        f"{content}\n"
        "----- END FILE CONTENTS -----"
    )


def append_file_to_prompt(prompt: str, file_path: Path, content: str) -> str:
    """
    Return prompt text with one file attachment block appended.

    This helper is intentionally small and reusable so Textual chat can
    adopt the same file attachment envelope later.
    """
    block = format_file_attachment(file_path.name, content)
    return f"{prompt}\n\n{block}"
