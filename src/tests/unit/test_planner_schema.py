import pytest
from pydantic import ValidationError

from src.internal.agents.planner.schema import RoutingPlan, planner_json_schema


def test_routing_plan_accepts_allowed_agent() -> None:
    p = RoutingPlan(agent="researcher", rationale="web")
    assert p.agent == "researcher"


def test_routing_plan_normalizes_case() -> None:
    p = RoutingPlan(agent="ARCHIVIST")
    assert p.agent == "archivist"


def test_routing_plan_rejects_unknown_agent() -> None:
    with pytest.raises(ValidationError):
        RoutingPlan(agent="not_a_real_agent")


def test_planner_json_schema_has_agent_enum() -> None:
    schema = planner_json_schema()
    enum = schema["properties"]["agent"]["enum"]
    assert "general" in enum
    assert "researcher" in enum
