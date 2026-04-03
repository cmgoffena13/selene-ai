import pytest
from pydantic import ValidationError

from src.internal.agents.planner.schema import RoutingPlan, planner_json_schema


def test_routing_plan_accepts_allowed_agent(planner_allows_all_agents: None) -> None:
    p = RoutingPlan(agent="researcher", rationale="web")
    assert p.agent == "researcher"


def test_routing_plan_normalizes_case(planner_allows_all_agents: None) -> None:
    p = RoutingPlan(agent="ARCHIVIST")
    assert p.agent == "archivist"


def test_routing_plan_rejects_unknown_agent(planner_allows_all_agents: None) -> None:
    with pytest.raises(ValidationError):
        RoutingPlan(agent="not_a_real_agent")


def test_planner_json_schema_has_agent_enum(planner_allows_all_agents: None) -> None:
    schema = planner_json_schema()
    enum = schema["properties"]["agent"]["enum"]
    assert "general" in enum
    assert "researcher" in enum


def test_planner_json_schema_always_includes_general() -> None:
    schema = planner_json_schema()
    assert "general" in schema["properties"]["agent"]["enum"]
