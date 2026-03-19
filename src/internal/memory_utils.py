from pathlib import Path

from src.utils import get_selene_ai_config_dir


def get_memory_dir() -> Path:
    """
    Return the directory where MEMORY files are stored.
    Uses ~/.config/selene_ai/memories; creates it if missing.
    """
    return get_selene_ai_config_dir("memories")


def get_memory_path(session_id: str, ext: str = ".pkl") -> Path:
    """
    Return the file path for a session's MEMORY (for save/load).
    """
    return get_memory_dir() / f"{session_id}{ext}"
