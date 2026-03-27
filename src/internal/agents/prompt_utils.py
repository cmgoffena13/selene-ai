import datetime
from pathlib import Path
from typing import Any

import orjson

SHARED_PROMPT_MAPPING = {"identity.md": 1, "files.md": 2}


def agents_root() -> Path:
    """Directory containing ``shared_prompts/`` and per-agent packages."""
    return Path(__file__).resolve().parent


def load_shared_prompt_sections() -> str:
    """
    Load shared markdown sections in :data:`SHARED_PROMPT_MAPPING` rank order.

    Every mapped file must exist under ``shared_prompts/``.
    """
    base = agents_root() / "shared_prompts"
    ordered = sorted(SHARED_PROMPT_MAPPING, key=lambda n: SHARED_PROMPT_MAPPING[n])
    parts: list[str] = []
    missing: list[str] = []
    for name in ordered:
        path = base / name
        if not path.is_file():
            missing.append(str(path))
            continue
        parts.append(path.read_text(encoding="utf-8"))
    if missing:
        raise FileNotFoundError("Missing shared prompt file(s): " + ", ".join(missing))
    return "\n\n".join(parts)


def load_agent_prompt(agent_name: str) -> str:
    path = agents_root() / agent_name / "prompt.md"
    if not path.is_file():
        raise FileNotFoundError(f"Missing agent prompt: {path}")
    return path.read_text(encoding="utf-8")


def compose_system_prompt(agent_name: str) -> str:
    """
    Full system prompt: shared sections (ordered), then ``<agent>/prompt.md``,
    with runtime placeholders (e.g. ``{current_date}``) filled in.
    """
    shared = load_shared_prompt_sections()
    agent = load_agent_prompt(agent_name)
    raw = f"{shared}\n\n{agent}"
    return inject_system_prompt_placeholders(raw)


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


def inject_system_prompt_placeholders(template: str) -> str:
    """
    Replace placeholders in the system prompt template (e.g. {current_date}).

    The date is computed when this runs (typically at process / agent init).
    Uses string replace instead of str.format so literals like ``{}`` or
    ``{{task}}`` in prompts are not interpreted as format fields.
    """
    current_date = datetime.datetime.today().strftime("%A, %B %d, %Y")
    return template.replace(f"{{current_date}}", current_date)


def format_tool_result(tool_name: str, query: str, result: Any) -> str:
    """Format one tool result block for prompt context."""
    if isinstance(result, str):
        result_content = result
    else:
        result_content = orjson.dumps(result).decode("utf-8")

    return (
        f"Tool: {tool_name}\n"
        f"Tool Query: {query}\n"
        "Tool Result:\n"
        "----- BEGIN TOOL RESULT -----\n"
        f"{result_content}\n"
        "----- END TOOL RESULT -----"
    )


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
