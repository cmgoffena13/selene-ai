import datetime
import json
from pathlib import Path
from typing import Any, Optional

from src.exceptions import AgentDoesNotExistError

PROMPT_MAPPING = {"identity.md": 1, "tools.md": 2, "files.md": 3}


def agent_prompts_dir(agent_name: str) -> Path:
    """Resolve ``src/internal/agents/<agent_name>/prompts``."""
    return Path(__file__).resolve().parent / agent_name / "prompts"


def agent_task_prompt(agent_name: str) -> Optional[str]:
    path = Path(__file__).resolve().parent / agent_name / "prompts" / "task.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def list_agent_prompt_files(agent_name: str) -> list[Path]:
    """All files under that agent's ``prompts`` directory (recursive), sorted."""
    root = agent_prompts_dir(agent_name)
    if not root.is_dir():
        raise AgentDoesNotExistError(f"Agent {agent_name} does not exist.")
    return sorted(p for p in root.rglob("*") if p.is_file())


def build_system_prompt(agent_name: str) -> str:
    """
    Concatenate prompt files for ``agent_name`` in :data:`PROMPT_MAPPING` order.

    Only files that exist under that agent's ``prompts/`` tree and whose basenames
    appear in the mapping are included; missing mapped names are skipped.
    """
    all_files = list_agent_prompt_files(agent_name)
    by_name = {p.name: p for p in all_files if p.name in PROMPT_MAPPING}
    ordered_names = sorted(PROMPT_MAPPING, key=lambda n: PROMPT_MAPPING[n])
    parts = [
        by_name[n].read_text(encoding="utf-8") for n in ordered_names if n in by_name
    ]
    return "\n\n".join(parts)


def inject_system_prompt_placeholders(template: str) -> str:
    """
    Replace placeholders in the system prompt template (e.g. {current_date}).

    The date is computed when this runs (typically at process / agent init).
    Uses string replace instead of str.format so literals like ``{}`` or
    ``{{task}}`` in prompts are not interpreted as format fields.
    """
    current_date = datetime.datetime.today().strftime("%A, %B %d, %Y")
    return template.replace("{current_date}", current_date)


def format_tool_result(tool_name: str, query: str, result: Any) -> str:
    """Format one tool result block for prompt context."""
    if isinstance(result, str):
        result_content = result
    else:
        result_content = json.dumps(result)

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
