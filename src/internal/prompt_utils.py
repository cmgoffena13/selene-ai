from datetime import date
from pathlib import Path


def inject_system_prompt_placeholders(template: str) -> str:
    """
    Replace placeholders in the system prompt template (e.g. {current_date}).

    The date is computed when this runs (typically at process / agent init).
    """
    current_date = date.today().isoformat()
    return template.format(current_date=current_date)


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
