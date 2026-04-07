from typing import Optional

import structlog
from tavily import TavilyClient
from thoughtflow import TOOL

from src.internal.agents.researcher.schema import WebSearchHit, WebSearchToolResult
from src.settings import config

logger = structlog.getLogger(__name__)

# https://docs.tavily.com/documentation/api-reference/endpoint/search
_VALID_TOPICS = frozenset({"general", "news", "finance"})
_VALID_TIME_RANGES = frozenset({"day", "week", "month", "year", "d", "w", "m", "y"})
DEFAULT_TIME_RANGE = "year"

WEB_SEARCH_DESCRIPTION = """
Search the web (Tavily).

**How the agent invokes this tool:** the model must emit JSON that the runtime
recognizes as a tool call, e.g. `{"name":"web_search","arguments":{...}}`.
The `arguments` object must satisfy the fields below — that is separate from
the JSON **result** the tool returns after running (hits, `total_found`, etc.).

**Arguments (all required unless noted):** `query` (search string), `topic`
(`general` | `news` | `finance`), `time_range` (`day` | `week` | `month` | `year`).
Optional: `max_results` (default 5). For breaking news prefer `topic=news` and
often `time_range=week`. Empty `query` returns an empty result without calling Tavily.
"""

WEB_SEARCH_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {
            "type": "integer",
            "description": "Max results (default 5)",
            "default": 5,
        },
        "topic": {
            "type": "string",
            "description": (
                "Tavily search category: 'general', 'news' for real-time "
                "and current-events coverage, 'finance' for markets and business."
            ),
            "enum": ["general", "news", "finance"],
        },
        "time_range": {
            "type": "string",
            "description": (
                "Only return pages published or updated within this window before today "
                "(by source date). Use 'week' when you need very recent results."
            ),
            "enum": ["day", "week", "month", "year"],
        },
    },
    "required": ["query", "topic", "time_range"],
}


def _tavily_search(**kwargs) -> str:
    """Call Tavily search API."""
    logger.info("Tavily Search kwargs", kwargs=kwargs)
    try:
        query = (kwargs.get("query") or "").strip()
        if not query:
            payload = WebSearchToolResult(query="", results=[], total_found=0)
            return payload.model_dump_json()

        try:
            max_results = max(0, min(20, int(kwargs.get("max_results", 5))))
        except (TypeError, ValueError):
            max_results = 5

        topic = kwargs.get("topic")
        if topic not in _VALID_TOPICS:
            topic = "general"

        time_range = kwargs.get("time_range")
        if time_range not in _VALID_TIME_RANGES:
            time_range = DEFAULT_TIME_RANGE

        search_kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "topic": topic,
            "time_range": time_range,
        }

        response = TavilyClient(api_key=config.SELENE_TAVILY_API_KEY).search(
            **search_kwargs
        )
        raw = response.get("results", []) if isinstance(response, dict) else []
        hits = [
            WebSearchHit(
                title=row.get("title", ""),
                url=row.get("url", ""),
                snippet=row.get("content", ""),
                published_date=row.get("published_date", ""),
                rank=index + 1,
                source=(row.get("url") or "")[:100],
            )
            for index, row in enumerate(raw)
        ]
        payload = WebSearchToolResult(
            query=query,
            provider="tavily",
            topic=topic,
            time_range=time_range,
            results=hits,
            total_found=len(hits),
        )
        out = payload.model_dump_json()
        logger.debug("Web search result", result=out)
        return out
    except Exception as e:
        logger.error("Web search error", error=e)
        raise e


def get_web_search_tool() -> Optional[TOOL]:
    """Get the web search tool."""
    if config.SELENE_TAVILY_API_KEY is None:
        return None
    else:
        return TOOL(
            name="web_search",
            description=WEB_SEARCH_DESCRIPTION,
            parameters=WEB_SEARCH_PARAMETERS,
            fn=_tavily_search,
        )
