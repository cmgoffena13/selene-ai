from unittest.mock import MagicMock

from thoughtflow import MEMORY

from src.internal.agents.planner.agent import PlannerAgent


def _mem_with_user(text: str) -> MEMORY:
    m = MEMORY()
    m.add_msg("user", text)
    return m


def test_planner_call_valid_first_try(planner_system_prompt: str) -> None:
    llm = MagicMock()
    llm.call.return_value = ['{"agent": "general", "rationale": "greeting"}']
    agent = PlannerAgent(
        system_prompt=planner_system_prompt,
        llm=llm,
        name="planner",
        max_iterations=2,
    )
    out = agent(_mem_with_user("hi"))
    assert out.agent == "general"
    llm.call.assert_called_once()


def test_planner_call_retries_then_succeeds(
    planner_system_prompt: str,
    planner_allows_all_agents: None,
) -> None:
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
    out = agent(_mem_with_user("latest news?"))
    assert out.agent == "researcher"
    assert llm.call.call_count == 2


def test_planner_call_falls_back_after_three_failures(
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
    out = agent(_mem_with_user("x"))
    assert out.agent == "general"
    assert llm.call.call_count == 3
