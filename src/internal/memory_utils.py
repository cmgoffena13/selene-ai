from pathlib import Path


def get_memory_dir() -> Path:
    """
    Return the directory where MEMORY files are stored.
    Uses ~/.config/selene_ai/memories; creates it if missing.
    """
    memory_dir = Path.home() / ".config" / "selene_ai" / "memories"
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir


def get_memory_path(session_id: str, ext: str = ".pkl") -> Path:
    """
    Return the file path for a session's MEMORY (for save/load).
    """
    return get_memory_dir() / f"{session_id}{ext}"
