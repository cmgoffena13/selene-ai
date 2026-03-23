from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.internal.agents import prompt_utils as pu


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def prompt_agents_fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "prompt_agents"


@pytest.fixture
def patch_agent_prompts_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str, Path], None]:
    def _patch(agent_name: str, prompts_dir: Path) -> None:
        real = pu.agent_prompts_dir

        def patched(name: str) -> Path:
            if name == agent_name:
                return prompts_dir
            return real(name)

        monkeypatch.setattr(pu, "agent_prompts_dir", patched)

    return _patch
