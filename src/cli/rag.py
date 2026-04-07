import typer
from typer import Argument, Exit, Option

from src.internal.llm.ollama import warn_if_ollama_unreachable
from src.internal.ui.console import echo
from src.settings import config

rag_app = typer.Typer(
    help="Build and manage RAG indexes (stored in ~/.config/selene_ai)."
)

RAG_SUPPORTED_EXTENSIONS = (
    ".csv",
    ".docx",
    ".epub",
    ".gif",
    ".hwp",
    ".ipynb",
    ".jpeg",
    ".jpg",
    ".md",
    ".mbox",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".pptx",
    ".py",
    ".txt",
    ".webp",
    ".xls",
    ".xlsx",
)
RAG_SUPPORTED_EXTENSIONS_HELP = (
    "Supported: "
    + ", ".join(RAG_SUPPORTED_EXTENSIONS)
    + ". Other files are read as plain text."
)


@rag_app.command(
    "index",
    help=f"Create a RAG index from a directory. {RAG_SUPPORTED_EXTENSIONS_HELP}",
)
def rag_index(
    name: str = Argument(
        ..., help="Index name (e.g. my-docs). Used to look up the index later."
    ),
    dir: str = Option(
        ...,
        "--dir",
        "-d",
        help=f"Directory path of files to index (recursive).",
    ),
) -> None:
    from src.internal.rag.builder import build_rag_index

    warn_if_ollama_unreachable(config.SELENE_OLLAMA_HOST)
    try:
        path = build_rag_index(index_name=name, docs_dir=dir)
        echo(f"Index '{name}' built and registered at {path}")
    except NotADirectoryError as e:
        echo(f"Error: {e}", err=True)
        raise Exit(code=1)
    except ValueError as e:
        echo(f"Error: {e}", err=True)
        raise Exit(code=1)
    except Exception as e:
        echo(f"Error building index: {e}", err=True)
        raise Exit(code=1)
    raise Exit(code=0)


@rag_app.command(
    "update",
    help="Update an existing RAG index with new files from its stored docs directory (add-only for HNSW).",
)
def rag_update(
    name: str = Argument(..., help="Index name to update."),
) -> None:
    from src.internal.rag.updater import update_rag_index

    warn_if_ollama_unreachable(config.SELENE_OLLAMA_HOST)
    try:
        path = update_rag_index(index_name=name)
        echo(f"Index '{name}' updated at {path}")
    except NotADirectoryError as e:
        echo(f"Error: {e}", err=True)
        raise Exit(code=1)
    except ValueError as e:
        echo(f"Error: {e}", err=True)
        raise Exit(code=1)
    except Exception as e:
        echo(f"Error updating index: {e}", err=True)
        raise Exit(code=1)
    raise Exit(code=0)


@rag_app.command("list", help="List RAG indexes with size (GB) and docs directory.")
def rag_list() -> None:
    from src.internal.rag.rag_utils import list_rag_indexes_with_sizes

    indexes = list_rag_indexes_with_sizes()
    if not indexes:
        echo("No RAG indexes found.")
        return
    for name, _path, size_bytes, docs_dir in indexes:
        size_gb = size_bytes / (1024**3)
        echo(f"  {name}  {size_gb:.2f} GB  {docs_dir}")
    raise Exit(code=0)


@rag_app.command("delete", help="Delete a stored RAG index by name.")
def rag_delete(
    name: str = Argument(..., help="Index name to delete (e.g. my-docs)."),
) -> None:
    from src.internal.rag.rag_utils import delete_rag_index

    deleted = delete_rag_index(name)
    if deleted:
        echo(f"Index '{name}' deleted.")
    else:
        echo(f"Index '{name}' not found.")
    raise Exit(code=0)
