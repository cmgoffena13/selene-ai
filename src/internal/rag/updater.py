from collections import defaultdict
from pathlib import Path

import structlog
from leann import LeannBuilder
from leann.chunking_utils import create_traditional_chunks
from leann.cli import suppress_cpp_output
from leann.sync import FileSynchronizer
from llama_index.core import SimpleDirectoryReader

from src.internal.rag.rag_utils import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SYNC_SNAPSHOT_FILENAME,
    get_rag_index_docs_dir,
    get_rag_index_path,
)
from src.settings import config
from src.utils import read_json

logger = structlog.getLogger(__name__)


def update_rag_index(index_name: str) -> str:
    """
    Update an existing index with new files from its stored docs directory (HNSW: add-only).

    Uses the sync snapshot and docs_dir stored in the registry when the index was built.
    Removed or modified files are not reflected (HNSW does not support removal).

    Args:
        index_name: Name of the registered index.

    Returns:
        Absolute path to the index.

    Raises:
        ValueError: If the index does not exist.
    """
    path = get_rag_index_path(index_name)
    if path is None:
        raise ValueError(
            f"Index '{index_name}' not found. Build it first with `selene rag index {index_name} --docs <dir>`."
        )

    docs_dir = get_rag_index_docs_dir(index_name)
    if not docs_dir:
        raise ValueError(f"Index '{index_name}' has no stored docs directory.")
    index_path = str(path)
    index_dir = path.parent
    docs_path = Path(docs_dir).resolve()
    if not docs_path.is_dir():
        raise NotADirectoryError(f"Stored docs directory no longer exists: {docs_dir}")

    snapshot_path = index_dir / SYNC_SNAPSHOT_FILENAME
    if not snapshot_path.exists():
        raise ValueError(
            f"Index '{index_name}' has no sync snapshot (was it built with an older version?). Rebuild with `selene rag index {index_name} --docs <dir>`."
        )

    fs = FileSynchronizer(
        root_dir=str(docs_path),
        snapshot_path=str(snapshot_path),
        auto_load=True,
    )
    added, removed, modified = fs.detect_changes()

    if removed or modified:
        # HNSW cannot remove or update; snapshot will still be committed so we don't re-detect forever.
        logger.warning(
            f"Index '{index_name}' has removed or modified files. Rebuild with `selene rag index {index_name} --docs <dir>`."
        )
        pass  # Warn in CLI

    if not added and not removed and not modified:
        return index_path

    if not added:
        fs.commit()
        return index_path

    # Load only added files: group by parent dir and use input_files.
    added_abs = [str(docs_path / p) if not Path(p).is_absolute() else p for p in added]
    files_by_dir = defaultdict(list)
    for fp in added_abs:
        p = Path(fp)
        if p.exists():
            files_by_dir[str(p.parent)].append(str(p))

    documents = []
    for parent_dir, file_list in files_by_dir.items():
        try:
            docs = SimpleDirectoryReader(
                parent_dir,
                input_files=file_list,
                filename_as_id=True,
                exclude_hidden=False,
            ).load_data()
            documents.extend(docs)
        except Exception:
            continue

    if not documents:
        fs.commit()
        return index_path

    chunks = create_traditional_chunks(
        documents,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    # Use same backend and embedding as the existing index.
    meta_path = Path(index_path + ".meta.json")
    meta = read_json(meta_path)
    backend_name = meta["backend_name"]
    embedding_model = meta["embedding_model"]
    embedding_mode = meta.get("embedding_mode", "sentence-transformers")

    builder = LeannBuilder(
        backend_name=backend_name,
        embedding_model=embedding_model,
        embedding_mode=embedding_mode,
    )
    for c in chunks:
        builder.add_text(c["text"], metadata=c.get("metadata", {}))

    with suppress_cpp_output(suppress=config.LEANN_SUPPRESS_OUTPUT):
        builder.update_index(index_path)
    fs.commit()
    return index_path
