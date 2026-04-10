from typing import Any, Optional

import structlog
from leann import LeannSearcher
from leann.cli import suppress_cpp_output
from thoughtflow import TOOL

from src.internal.agents.archivist.schema import (
    LocalSearchErrorItem,
    LocalSearchHit,
    LocalSearchToolResult,
)
from src.internal.rag.rag_utils import list_rag_indexes_with_sizes
from src.settings import config

logger = structlog.getLogger(__name__)

_LOCAL_SEARCH_TOP_K = 5
_LOCAL_SEARCH_PER_INDEX_K = 5
_LOCAL_SEARCH_SNIPPET_CHARS = 600

# NOTE: LEANN raises this when grep mode has no passages file; show a clearer message to users.
_GREP_NO_PASSAGES_FILE_MSG = "No .jsonl passages file found for grep search"
_GREP_NO_PASSAGES_FILE_USER_MSG = "No files found."


def _local_search_error_text(exc: Exception) -> str:
    text = str(exc)
    if text == _GREP_NO_PASSAGES_FILE_MSG:
        return _GREP_NO_PASSAGES_FILE_USER_MSG
    return text


LOCAL_SEARCH_DESCRIPTION = """
Search across all locally-built LEANN RAG vector indexes.
This is useful for querying User's own local files and documents.
Set "use_grep" to True to search for quoted text in the indexes.
"""

LOCAL_SEARCH_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Semantic search query"},
        "use_grep": {
            "type": "boolean",
            "description": "If true, use LEANN grep search over indexed passages instead of vector similarity",
        },
    },
    "required": ["query", "use_grep"],
}


def _local_search(**kwargs: Any) -> str:
    """Perform a local LEANN search."""
    logger.info("Local Search kwargs", kwargs=kwargs)
    try:
        query = (kwargs.get("query") or "").strip()
        if not query:
            payload = LocalSearchToolResult(
                query="",
                indexes_searched=0,
                results=[],
                errors=[],
            )
            return payload.model_dump_json()

        use_grep = bool(kwargs.get("use_grep", False))

        indexes = list_rag_indexes_with_sizes()
        if not indexes:
            payload = LocalSearchToolResult(
                query=query,
                indexes_searched=0,
                results=[],
                errors=[],
            )
            return payload.model_dump_json()

        aggregated: list[dict[str, Any]] = []
        for index_name, index_path, _size_bytes, _docs_dir in indexes:
            try:
                with suppress_cpp_output(suppress=config.LEANN_SUPPRESS_OUTPUT):
                    searcher = LeannSearcher(
                        str(index_path),
                        enable_warmup=False,
                        # Keep recompute embeddings enabled for pruned-node scenarios.
                        recompute_embeddings=True,
                        use_daemon=True,
                    )
                    hits = searcher.search(
                        query, top_k=_LOCAL_SEARCH_PER_INDEX_K, use_grep=use_grep
                    )
            except Exception as e:
                aggregated.append(
                    {
                        "index": index_name,
                        "error": _local_search_error_text(e),
                        "hits": [],
                    }
                )
                continue

            for h in hits:
                snippet = (h.text or "").strip()
                if (
                    _LOCAL_SEARCH_SNIPPET_CHARS
                    and len(snippet) > _LOCAL_SEARCH_SNIPPET_CHARS
                ):
                    snippet = snippet[:_LOCAL_SEARCH_SNIPPET_CHARS] + "…"

                aggregated.append(
                    {
                        "index": index_name,
                        "id": h.id,
                        "score": h.score,
                        "text": snippet,
                        "metadata": h.metadata or {},
                    }
                )

        # Keep only the highest scoring results; ignore error blobs for ranking.
        scored = [r for r in aggregated if "score" in r]
        scored.sort(key=lambda x: float(x["score"]), reverse=True)
        final = scored[:_LOCAL_SEARCH_TOP_K]

        # If some indexes errored, include their errors too (but don’t let them break ranking).
        errors_raw = [r for r in aggregated if "error" in r]
        payload = LocalSearchToolResult(
            query=query,
            indexes_searched=len(indexes),
            results=[LocalSearchHit.model_validate(h) for h in final],
            errors=[LocalSearchErrorItem.model_validate(e) for e in errors_raw],
        )
        result = payload.model_dump_json()
        logger.debug("Local search result", result=result)
        return result
    except Exception as e:
        logger.error("Local search error", error=e)
        raise e


def get_local_search_tool() -> Optional[TOOL]:
    """Get the local search tool."""
    indexes = list_rag_indexes_with_sizes()
    if not indexes:
        return None
    return TOOL(
        name="local_search",
        description=LOCAL_SEARCH_DESCRIPTION,
        parameters=LOCAL_SEARCH_PARAMETERS,
        fn=_local_search,
    )
