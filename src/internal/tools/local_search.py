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

LOCAL_SEARCH_DESCRIPTION = """
Search across all locally-built RAG vector indexes.
This is useful for searching through the user's own local files and documents.
Set "use_grep" to True to search for quoted text in the indexes.
"""

LOCAL_SEARCH_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "use_grep": {
            "type": "boolean",
            "description": "If true, use LEANN grep search over indexed passages instead of vector similarity (default: false)",
            "default": False,
        },
        "top_k": {
            "type": "integer",
            "description": "Max results to return across all indexes (default 5)",
            "default": 5,
        },
        "per_index_k": {
            "type": "integer",
            "description": "How many results to fetch per index before aggregating (default 5)",
            "default": 5,
        },
        "text_snippet_chars": {
            "type": "integer",
            "description": "Max characters per result snippet (default 600)",
            "default": 600,
        },
    },
    "required": ["query"],
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

        try:
            top_k = max(1, int(kwargs.get("top_k", 5)))
        except (TypeError, ValueError):
            top_k = 5

        try:
            per_index_k = max(1, int(kwargs.get("per_index_k", top_k)))
        except (TypeError, ValueError):
            per_index_k = top_k

        try:
            text_snippet_chars = max(0, int(kwargs.get("text_snippet_chars", 600)))
        except (TypeError, ValueError):
            text_snippet_chars = 600

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
                    hits = searcher.search(query, top_k=per_index_k, use_grep=use_grep)
            except Exception as e:
                aggregated.append(
                    {
                        "index": index_name,
                        "error": str(e),
                        "hits": [],
                    }
                )
                continue

            for h in hits:
                snippet = (h.text or "").strip()
                if text_snippet_chars and len(snippet) > text_snippet_chars:
                    snippet = snippet[:text_snippet_chars] + "…"

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
        final = scored[:top_k]

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
