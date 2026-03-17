from typing import Any, Optional

import structlog
from thoughtflow import TOOL

logger = structlog.getLogger(__name__)


def _coerce_max_results(val: Any, default: int = 5) -> int:
    if val is None:
        return default
    # Sometimes the model incorrectly passes the JSON schema object for the parameter.
    if isinstance(val, dict):
        return default
    try:
        n = int(val)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, 20))


def _search_impl(query: str, max_results: Any = 5) -> str:
    """Run Tavily search and return a single string for the LLM."""
    from tavily import TavilyClient

    from src.settings import config

    if not config.TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY is not set. Web search is unavailable.")
        return "Error: TAVILY_API_KEY is not set. Web search is unavailable."

    max_results_n = _coerce_max_results(max_results, default=5)
    client = TavilyClient(api_key=config.TAVILY_API_KEY)
    response = client.search(
        query=query, max_results=max_results_n, search_depth="basic"
    )
    raw = getattr(response, "results", None) or (
        response.get("results", []) if isinstance(response, dict) else []
    )
    if not raw:
        logger.error(f"No results found for query: {query}")
        return "No results found."
    lines = []
    for i, r in enumerate(raw, 1):
        title = (
            (r.get("title") or r.get("name") or "(no title)")
            if isinstance(r, dict)
            else getattr(r, "title", None) or getattr(r, "name", "(no title)")
        )
        url = r.get("url") if isinstance(r, dict) else getattr(r, "url", "")
        content = (
            (r.get("content") or "")[:300]
            if isinstance(r, dict)
            else (getattr(r, "content", None) or "")[:300]
        )
        lines.append(f"{i}. {title}\n   URL: {url}\n   {content.strip()}")
    return "\n\n".join(lines)


def get_web_search_tool() -> Optional[TOOL]:
    """
    Return a thoughtflow TOOL for web search if TAVILY_API_KEY is set, else None.
    """
    from src.settings import config

    if not config.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY is not set. Web search is unavailable.")
        return None
    return TOOL(
        name="web_search",
        description="Search the web for current or factual information. Use when you need up-to-date or real-world facts.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        fn=_search_impl,
    )
