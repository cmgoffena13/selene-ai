from unittest.mock import MagicMock

from src.internal.agents.planner.agent import PlannerAgent


def test_generate_agent_route_valid_first_try(planner_system_prompt: str) -> None:
    llm = MagicMock()
    llm.call.return_value = ['{"agent": "general", "rationale": "greeting"}']
    agent = PlannerAgent(
        system_prompt=planner_system_prompt,
        llm=llm,
        name="planner",
        max_iterations=2,
    )
    out = agent.generate_agent_route("hi")
    assert out.agent == "general"
    llm.call.assert_called_once()


def test_generate_agent_route_retries_then_succeeds(planner_system_prompt: str) -> None:
    llm = MagicMock()
    llm.call.side_effect = [
        ["not json"],
        ['{"agent": "researcher", "rationale": "news"}'],
    ]
    agent = PlannerAgent(
        system_prompt=planner_system_prompt,
        llm=llm,
        name="planner",
        max_iterations=2,
    )
    out = agent.generate_agent_route("latest news?")
    assert out.agent == "researcher"
    assert llm.call.call_count == 2


def test_generate_agent_route_falls_back_after_three_failures(
    planner_system_prompt: str,
) -> None:
    llm = MagicMock()
    llm.call.return_value = ["invalid"]
    agent = PlannerAgent(
        system_prompt=planner_system_prompt,
        llm=llm,
        name="planner",
        max_iterations=2,
    )
    out = agent.generate_agent_route("x")
    assert out.agent == "general"
    assert llm.call.call_count == 3
