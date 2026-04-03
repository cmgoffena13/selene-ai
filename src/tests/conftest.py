import pytest
from typer.testing import CliRunner

from src.internal.agents.factory import AgentFactory


def _all_routable_agents(cls) -> tuple[str, ...]:
    return ("researcher", "archivist", "general")


@pytest.fixture
def planner_allows_all_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    """Planner tests that need ``researcher`` / ``archivist`` in the routing enum."""
    monkeypatch.setattr(
        AgentFactory, "get_agent_names", classmethod(_all_routable_agents)
    )


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def planner_system_prompt() -> str:
    return "You are a planner. {{agent_list}}"
