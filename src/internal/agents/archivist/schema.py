from typing import Any

from pydantic import BaseModel, Field


class LocalSearchHit(BaseModel):
    """One ranked hit from a vector / grep search over a single index."""

    index: str
    id: int | str
    score: float
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalSearchErrorItem(BaseModel):
    """Per-index failure when opening or searching an index."""

    index: str
    error: str
    hits: list[Any] = Field(default_factory=list)


class LocalSearchToolResult(BaseModel):
    """
    Standard payload for the ``local_search`` tool (before prompt wrapping).

    Always includes ``query`` and ``indexes_searched`` so callers can validate
    every code path the same way.
    """

    query: str
    indexes_searched: int
    results: list[LocalSearchHit]
    errors: list[LocalSearchErrorItem] = Field(default_factory=list)


def local_search_tool_result_json_schema() -> dict:
    """JSON Schema for ``LocalSearchToolResult`` (tool output, not LLM tool-call JSON)."""
    return LocalSearchToolResult.model_json_schema()
