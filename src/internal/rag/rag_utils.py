import json
import shutil
from pathlib import Path

from src.utils import get_selene_ai_config_dir

CHUNK_SIZE = 256
CHUNK_OVERLAP = 128
SYNC_SNAPSHOT_FILENAME = "sync_context.pickle"


def get_rag_indexes_dir() -> Path:
    """Directory where index files are stored (~/.config/selene_ai/indexes)."""
    return get_selene_ai_config_dir("indexes")


def get_rag_registry_path() -> Path:
    """Path to the JSON file mapping index name -> absolute index path."""
    return get_rag_indexes_dir() / "rag_indexes.json"


def load_rag_registry() -> dict[str, dict]:
    """Load { index_name: { path, docs_dir } } from disk. Returns {} if missing or invalid."""
    path = get_rag_registry_path()
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_rag_registry(registry: dict[str, dict]) -> None:
    """Write { index_name: { path, docs_dir } } to disk."""
    path = get_rag_registry_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def register_rag_index(name: str, index_path: str, docs_dir: str) -> None:
    """Add or overwrite an index in the registry (path and docs_dir)."""
    reg = load_rag_registry()
    reg[name] = {
        "path": str(Path(index_path).resolve()),
        "docs_dir": str(Path(docs_dir).resolve()),
    }
    save_rag_registry(reg)


def get_rag_index_path(name: str) -> Path | None:
    """Return the stored index path for a named index, or None if not found."""
    reg = load_rag_registry()
    entry = reg.get(name)
    if not entry:
        return None
    p = Path(entry["path"])
    # LEANN stores an index as a *prefix* (e.g. ".../index") with multiple files
    # like ".../index.meta.json". The bare prefix path may not exist, so
    # existence is determined by the meta file.
    meta_path = Path(str(p) + ".meta.json")
    return p if meta_path.exists() else None


def get_rag_index_docs_dir(name: str) -> str | None:
    """Return the stored docs directory for a named index, or None if not found."""
    reg = load_rag_registry()
    entry = reg.get(name)
    if not entry:
        return None
    return entry["docs_dir"]


def _dir_size_bytes(path: Path) -> int:
    """Total size in bytes of all files under path (recursive)."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    except OSError:
        pass
    return total


def list_rag_indexes_with_sizes() -> list[tuple[str, Path, int, str]]:
    """Return (name, index_path, size_bytes, docs_dir) for each registered index that still exists on disk."""
    reg = load_rag_registry()
    out: list[tuple[str, Path, int, str]] = []
    for name, entry in reg.items():
        if name == "rag_indexes.json":
            continue
        p = Path(entry["path"])
        meta_path = Path(str(p) + ".meta.json")
        if not meta_path.exists():
            continue
        index_dir = p.parent
        size_bytes = _dir_size_bytes(index_dir)
        out.append((name, p, size_bytes, entry["docs_dir"]))
    return out


def delete_rag_index(name: str) -> bool:
    """
    Delete a stored RAG index by name.

    Deletes only the index directory under `indexes/<name>` and removes the
    entry from `rag_indexes.json`. Does NOT touch the original `docs_dir`.

    Returns:
        True if the index directory and/or registry entry existed and were removed.
    """
    deleted_any = False

    index_dir = get_rag_indexes_dir() / name
    if index_dir.exists():
        shutil.rmtree(index_dir)
        deleted_any = True

    reg = load_rag_registry()
    if name in reg:
        reg.pop(name, None)
        save_rag_registry(reg)
        deleted_any = True

    return deleted_any
