from tavily import TavilyClient
from thoughtflow import TOOL

from src.settings import config

WEB_SEARCH_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {
            "type": "integer",
            "description": "Max results (default 5)",
            "default": 5,
        },
    },
    "required": ["query"],
}


def _tavily_search(**kwargs):
    """Call Tavily search API. Expects query and optional max_results (int)."""
    query = (kwargs.get("query") or "").strip()
    if not query:
        return {"query": "", "results": [], "total_found": 0}
    try:
        max_results = max(0, min(20, int(kwargs.get("max_results", 5))))
    except (TypeError, ValueError):
        max_results = 5

    response = TavilyClient(api_key=config.TAVILY_API_KEY).search(
        query=query, max_results=max_results
    )
    raw = response.get("results", []) if isinstance(response, dict) else []
    results = [
        {
            "title": row.get("title", ""),
            "url": row.get("url", ""),
            "snippet": row.get("content", ""),
            "rank": index + 1,
            "source": (row.get("url") or "")[:100],
        }
        for index, row in enumerate(raw)
    ]
    return {
        "query": response.get("query", query) if isinstance(response, dict) else query,
        "provider": "tavily",
        "results": results,
        "total_found": len(results),
    }


def get_web_search_tool() -> TOOL:
    if config.TAVILY_API_KEY is None:
        return None
    else:
        return TOOL(
            name="web_search",
            description="Search the web for current or factual information. Use when you need up-to-date or real-world facts.",
            parameters=WEB_SEARCH_PARAMETERS,
            fn=_tavily_search,
        )
