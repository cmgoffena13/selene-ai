from functools import lru_cache

from pydantic import BaseModel, Field, field_validator

from src.internal.agents.factory import AgentFactory


class RoutingPlan(BaseModel):
    """Validated JSON output from the planner; must match ``planner_json_schema()``."""

    specialist: str = Field(
        ...,
        description="Exactly one target specialist name that should handle the user message.",
    )
    rationale: str | None = Field(
        None,
        description="Short justification for the routing choice.",
    )
    specialist_hint: str | None = Field(
        None,
        description="Guide specialist with information to help it achieve its goal.",
    )

    @field_validator("specialist")
    @classmethod
    def specialist_must_be_allowed(cls, v: str) -> str:
        low = v.strip().lower()
        allowed = set(AgentFactory.get_agent_names())
        if low not in allowed:
            raise ValueError(f"specialist must be one of {sorted(allowed)}, got {v!r}")
        return low


@lru_cache()
def planner_json_schema() -> dict:
    """
    JSON Schema for Ollama ``format`` (merged into ThoughtFlow LLM ``default_params``).

    Includes an ``enum`` on ``specialist`` so the model sees allowed names explicitly.
    """
    schema = RoutingPlan.model_json_schema()
    names = list(AgentFactory.get_agent_names())
    props = schema.setdefault("properties", {})
    agent_prop = props.setdefault("specialist", {})
    agent_prop["enum"] = names
    return schema
