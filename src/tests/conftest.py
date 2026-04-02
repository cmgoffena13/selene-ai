from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def planner_system_prompt() -> str:
    return "You are a planner. {{agent_list}}"
