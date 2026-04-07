from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.internal.agents import prompt_utils as pu


@pytest.fixture
def isolated_agents_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Minimal agents tree: one agent with ``prompt.md``."""
    root = tmp_path
    agent = root / "fixture_agent"
    agent.mkdir()
    (agent / "prompt.md").write_text("# agent-block\n", encoding="utf-8")
    monkeypatch.setattr(pu, "agents_root", lambda: root)
    return root


def test_agents_root_is_internal_agents_package() -> None:
    assert pu.agents_root().name == "agents"


def test_load_agent_prompt_reads_file(isolated_agents_root: Path) -> None:
    text = pu.load_agent_prompt("fixture_agent")
    assert "# agent-block" in text


def test_load_agent_prompt_injects_current_date(isolated_agents_root: Path) -> None:
    p = isolated_agents_root / "fixture_agent" / "prompt.md"
    p.write_text("Date: {current_date}\n", encoding="utf-8")
    text = pu.load_agent_prompt("fixture_agent")
    assert "{current_date}" not in text
    assert text.startswith("Date: ")


def test_load_agent_prompt_missing_raises(isolated_agents_root: Path) -> None:
    (isolated_agents_root / "fixture_agent" / "prompt.md").unlink()
    with pytest.raises(FileNotFoundError):
        pu.load_agent_prompt("fixture_agent")


def test_ensure_agent_prompt_file_creates_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    monkeypatch.setattr(pu, "agents_root", lambda: root)
    path = pu.ensure_agent_prompt_file("new_agent")
    assert path.name == "prompt.md"
    assert path.read_text(encoding="utf-8").startswith("# new_agent")


def test_inject_system_prompt_placeholders_replaces_date() -> None:
    out = pu.inject_system_prompt_placeholders("Today is {current_date}.")
    assert "{current_date}" not in out
    assert "Today is " in out


def test_append_file_to_prompt_appends_block() -> None:
    out = pu.append_file_to_prompt("hello", Path("/tmp/x.py"), "line1")
    assert out.startswith("hello\n\n")
    assert "x.py" in out
    assert "line1" in out
    assert "BEGIN FILE CONTENTS" in out
    assert "END FILE CONTENTS" in out


def test_specialist_tool_payload_text_prefers_tool_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pu, "extract_tool_result_payload", lambda m: "from_tool")
    assert pu.specialist_tool_payload_text(MagicMock()) == "from_tool"


def test_specialist_tool_payload_text_falls_back_to_assistant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pu, "extract_tool_result_payload", lambda m: None)
    mem = MagicMock()
    mem.last_asst_msg.return_value = "  assistant  "
    assert pu.specialist_tool_payload_text(mem) == "assistant  "


def test_specialist_validation_retry_feedback_includes_tool_and_error() -> None:
    out = pu.specialist_validation_retry_feedback("web_search", "bad json")
    assert "web_search" in out
    assert "bad json" in out
    assert "tool-call JSON only" in out


def test_specialist_tool_payload_text_fallback_when_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pu, "extract_tool_result_payload", lambda m: None)
    mem = MagicMock()
    mem.last_asst_msg.return_value = ""
    assert pu.specialist_tool_payload_text(mem) == "No input from sub agent."
