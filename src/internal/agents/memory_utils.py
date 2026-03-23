import json
from datetime import datetime
from pathlib import Path

from src.utils import get_selene_ai_config_dir


def get_chat_sessions_dir() -> Path:
    """Return the directory for saved Textual chat sessions."""
    return get_selene_ai_config_dir("chat_sessions")


def get_chat_sessions_index_path() -> Path:
    """Return the chat sessions index JSON path."""
    return get_chat_sessions_dir() / "sessions_index.json"


def new_chat_session_filename() -> str:
    """Create a timestamped JSON filename for a chat session."""
    return f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"


def new_chat_session_path() -> Path:
    """Return a new timestamped chat session path."""
    return get_chat_sessions_dir() / new_chat_session_filename()


def list_chat_session_files() -> list[Path]:
    """List saved chat session JSON files, newest first (excludes sessions_index.json)."""
    d = get_chat_sessions_dir()
    index_name = get_chat_sessions_index_path().name
    paths = [p for p in d.glob("*.json") if p.name != index_name]
    return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)


def resolve_chat_session_path(filename: str) -> Path:
    """Resolve a session filename to an absolute path in the sessions dir."""
    return get_chat_sessions_dir() / filename


def _read_sessions_index() -> list[dict[str, str]]:
    index_path = get_chat_sessions_index_path()
    if not index_path.exists():
        _write_sessions_index([])
        return []

    try:
        with index_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        _write_sessions_index([])
        return []

    if not isinstance(data, list):
        _write_sessions_index([])
        return []

    entries: list[dict[str, str]] = []
    for item in data:
        filename = str(item.get("filename", "")).strip()
        first_prompt = " ".join(str(item.get("first_prompt", "")).split())
        entries.append({"filename": filename, "first_prompt": first_prompt})
    return entries


def _write_sessions_index(entries: list[dict[str, str]]) -> None:
    index_path = get_chat_sessions_index_path()
    with index_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def list_chat_sessions_index() -> list[dict[str, str]]:
    """
    Return tracked sessions from index as:
    [{ "filename": "...json", "first_prompt": "..." }, ...]

    Also includes session JSON files on disk not yet in the index. Never includes sessions_index.json.
    """
    index_name = get_chat_sessions_index_path().name
    entries = [e for e in _read_sessions_index() if e.get("filename") != index_name]
    by_filename = {entry["filename"]: dict(entry) for entry in entries}
    for path in list_chat_session_files():
        by_filename.setdefault(path.name, {"filename": path.name, "first_prompt": ""})
    combined = list(by_filename.values())
    combined.sort(key=lambda item: item["filename"], reverse=True)
    return combined


def upsert_chat_session_index(filename: str, first_prompt: str = "") -> None:
    """Insert/update one session index entry by filename."""
    filename = (filename or "").strip()

    entries = _read_sessions_index()
    by_filename = {entry["filename"]: entry for entry in entries}

    normalized_prompt = " ".join((first_prompt or "").split())
    existing = by_filename.get(filename)
    if existing is None:
        by_filename[filename] = {
            "filename": filename,
            "first_prompt": normalized_prompt,
        }
    else:
        if not existing.get("first_prompt") and normalized_prompt:
            existing["first_prompt"] = normalized_prompt

    merged = list(by_filename.values())
    merged.sort(key=lambda item: item["filename"], reverse=True)
    _write_sessions_index(merged)


def delete_chat_session(filename: str) -> None:
    """Delete a saved chat session file and remove it from index."""
    path = resolve_chat_session_path(filename)
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass

    entries = _read_sessions_index()
    filtered = [entry for entry in entries if entry["filename"] != filename]
    filtered.sort(key=lambda item: item["filename"], reverse=True)
    _write_sessions_index(filtered)
