import structlog
from tavily import TavilyClient
from thoughtflow import TOOL

from src.internal.prompt_utils import format_tool_result
from src.settings import config

logger = structlog.getLogger(__name__)

# https://docs.tavily.com/documentation/api-reference/endpoint/search
_VALID_TOPICS = frozenset({"general", "news", "finance"})
_VALID_TIME_RANGES = frozenset({"day", "week", "month", "year", "d", "w", "m", "y"})
DEFAULT_TIME_RANGE = "year"

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
                "Tavily search category: 'general' (default), 'news' for real-time "
                "and current-events coverage, 'finance' for markets and business."
            ),
            "enum": ["general", "news", "finance"],
            "default": "general",
        },
        "time_range": {
            "type": "string",
            "description": (
                "Only return pages published or updated within this window before today "
                "(by source date). Defaults to 'year' when omitted. Use 'day' or 'week' "
                "when you need very recent results."
            ),
            "enum": ["day", "week", "month", "year"],
            "default": "year",
        },
    },
    "required": ["query"],
}


def _tavily_search(**kwargs):
    """Call Tavily search API."""
    logger.debug("Tavily search kwargs", kwargs=kwargs)
    try:
        query = (kwargs.get("query") or "").strip()
        if not query:
            return {"query": "", "results": [], "total_found": 0}
        try:
            max_results = max(0, min(20, int(kwargs.get("max_results", 5))))
        except (TypeError, ValueError):
            max_results = 5

        topic = kwargs.get("topic") or "general"
        if topic not in _VALID_TOPICS:
            topic = "general"

        time_range = kwargs.get("time_range")
        if time_range is not None and time_range not in _VALID_TIME_RANGES:
            time_range = None
        if time_range is None:
            time_range = DEFAULT_TIME_RANGE

        search_kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "topic": topic,
            "time_range": time_range,
        }

        response = TavilyClient(api_key=config.TAVILY_API_KEY).search(**search_kwargs)
        raw = response.get("results", []) if isinstance(response, dict) else []
        results = [
            {
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "snippet": row.get("content", ""),
                "published_date": row.get("published_date", ""),
                "rank": index + 1,
                "source": (row.get("url") or "")[:100],
            }
            for index, row in enumerate(raw)
        ]
        payload = {
            "query": query,
            "provider": "tavily",
            "topic": topic,
            "time_range": time_range,
            "results": results,
            "total_found": len(results),
        }
        result = format_tool_result(
            "web_search",
            payload["query"],
            payload,
        )
        logger.debug("Web search result", result=result)
        return result
    except Exception as e:
        logger.error("Web search error", error=e)
        raise e


def get_web_search_tool() -> TOOL:
    if config.SELENE_TAVILY_API_KEY is None:
        return None
    else:
        return TOOL(
            name="web_search",
            description=(
                "Search the web for current or factual information. For breaking news, "
                "sports, or politics use topic='news' and 'day' or 'week' for time_range. "
                "time_range defaults to one year when omitted. "
            ),
            parameters=WEB_SEARCH_PARAMETERS,
            fn=_tavily_search,
        )
