import pytest
from pydantic import ValidationError

from src.internal.agents.planner.schema import RoutingPlan, planner_json_schema


def test_routing_plan_accepts_allowed_specialist(
    planner_allows_all_agents: None,
) -> None:
    p = RoutingPlan(specialist="researcher", rationale="web")
    assert p.specialist == "researcher"


def test_routing_plan_normalizes_case(planner_allows_all_agents: None) -> None:
    p = RoutingPlan(specialist="ARCHIVIST")
    assert p.specialist == "archivist"


def test_routing_plan_rejects_unknown_specialist(
    planner_allows_all_agents: None,
) -> None:
    with pytest.raises(ValidationError):
        RoutingPlan(specialist="not_a_real_agent")


def test_planner_json_schema_has_specialist_enum(
    planner_allows_all_agents: None,
) -> None:
    schema = planner_json_schema()
    enum = schema["properties"]["specialist"]["enum"]
    assert "general" in enum
    assert "researcher" in enum


def test_planner_json_schema_always_includes_general() -> None:
    schema = planner_json_schema()
    assert "general" in schema["properties"]["specialist"]["enum"]
