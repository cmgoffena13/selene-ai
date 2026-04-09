import datetime
import json
from pathlib import Path
from typing import Any, Optional

from thoughtflow import MEMORY


def extract_tool_result_payload(memory: MEMORY) -> Optional[str]:
    """
    Inner tool output string from the last ``result`` message.

    ThoughtFlow stores tool results as JSON:
    ``{"name": "<tool>", "result": "<tool return string>"}``.
    When the model only calls tools (no assistant message), validation must read
    this, not ``last_asst_msg``.
    """
    output = None
    msgs = memory.get_msgs(include=["result"])
    if msgs:
        raw = msgs[-1].get("content")
        if raw is not None:
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                obj = None
            if isinstance(obj, dict):
                result = obj.get("result")
                if result is not None:
                    output = str(result).lstrip()
    return output


def specialist_tool_payload_text(memory: MEMORY) -> str:
    """Tool ``result`` payload if present; else last assistant text; else fixed fallback."""
    inner = extract_tool_result_payload(memory)
    if inner is not None:
        return inner
    last = memory.last_asst_msg(content_only=True)
    if not last:
        return "No input from sub agent."
    return last.lstrip()


def specialist_validation_retry_feedback(tool_name: str, last_err: str) -> str:
    """User message when specialist tool output fails Pydantic validation (retry loop)."""
    return (
        f"Either the {tool_name} tool did not run, or its result did not validate.\n"
        f"Details: {last_err}\n\n"
        f"To invoke the {tool_name} tool, your assistant reply must be tool-call JSON only. "
        "Reply with a single JSON object only; No markdown, no prose."
    )


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


def ensure_agent_prompt_file(
    agent_name: str, *, template: Optional[str] = None
) -> Path:
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


def apply_planner_agent_hint(system_prompt: str, agent_hint: Optional[str]) -> str:
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


def append_file_to_prompt(prompt: str, file_path: Path, content: str) -> str:
    """
    Return prompt text with one file attachment block appended.

    This helper is intentionally small and reusable so Textual chat can
    adopt the same file attachment envelope later.
    """
    block = (
        f"Filename: {file_path.name}\n"
        "File contents:\n"
        "----- BEGIN FILE CONTENTS -----\n"
        f"{content}\n"
        "----- END FILE CONTENTS -----"
    )
    return f"{prompt}\n\n{block}"
