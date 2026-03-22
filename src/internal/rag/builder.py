from pathlib import Path

from leann import LeannBuilder
from leann.chunking_utils import create_traditional_chunks
from leann.cli import suppress_cpp_output
from leann.sync import FileSynchronizer
from llama_index.core import SimpleDirectoryReader

from src.exceptions import DuplicateIndexError
from src.internal.rag.rag_utils import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    OLLAMA_EMBEDDING_MODEL,
    SYNC_SNAPSHOT_FILENAME,
    get_rag_index_path,
    get_rag_indexes_dir,
    register_rag_index,
)
from src.settings import config


def build_rag_index(
    index_name: str, docs_dir: str | Path, *, backend: str = "hnsw"
) -> str:
    """
    Build a LEANN index from a directory using Ollama embeddings and register it.

    Args:
        index_name: Name of the index (used for lookup later).
        docs_dir: Directory path to load documents from (recursive).
        backend: LEANN backend name ("hnsw", "diskann", or "ivf").

    Returns:
        Absolute path to the built index (same path stored in config).

    Raises:
        ValueError: If an index with this name already exists.
    """
    if get_rag_index_path(index_name) is not None:
        raise DuplicateIndexError(
            f"Index '{index_name}' already exists. Use a different name or remove it first."
        )

    docs_path = Path(docs_dir).resolve()
    if not docs_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {docs_dir}")

    index_dir = get_rag_indexes_dir() / index_name
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = str(index_dir / "index")

    documents = SimpleDirectoryReader(
        input_dir=str(docs_path),
        recursive=True,
        filename_as_id=True,
    ).load_data()

    if not documents:
        raise ValueError(f"No documents found under {docs_path}")

    chunks = create_traditional_chunks(
        documents,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    builder = LeannBuilder(
        backend_name=backend,
        embedding_model=OLLAMA_EMBEDDING_MODEL,
        embedding_mode="ollama",
    )
    for c in chunks:
        builder.add_text(c["text"], metadata=c.get("metadata", {}))

    with suppress_cpp_output(suppress=config.LEANN_SUPPRESS_OUTPUT):
        builder.build_index(index_path)

    register_rag_index(index_name, index_path, docs_dir=str(docs_path))

    # Snapshot docs_dir so future updates can detect added/removed/modified files.
    snapshot_path = index_dir / SYNC_SNAPSHOT_FILENAME
    fs = FileSynchronizer(
        root_dir=str(docs_path),
        snapshot_path=str(snapshot_path),
        auto_load=False,
    )
    fs.create_snapshot()

    return str(Path(index_path).resolve())
