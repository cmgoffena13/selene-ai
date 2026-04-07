from functools import lru_cache

from pydantic import BaseModel


class WebSearchHit(BaseModel):
    """One Tavily result row."""

    title: str
    url: str
    snippet: str
    published_date: str
    rank: int
    source: str


class WebSearchToolResult(BaseModel):
    """Standard payload for the ``web_search`` tool (before prompt wrapping)."""

    query: str
    provider: str = "tavily"
    topic: str = "general"
    time_range: str = "year"
    results: list[WebSearchHit]
    total_found: int


@lru_cache()
def web_search_tool_result_json_schema() -> dict:
    """JSON Schema for ``WebSearchToolResult``."""
    return WebSearchToolResult.model_json_schema()
