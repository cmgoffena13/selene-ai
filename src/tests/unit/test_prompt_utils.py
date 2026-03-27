from pathlib import Path

import pytest

from src.internal.agents import prompt_utils as pu


@pytest.fixture
def isolated_agents_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Minimal agents tree: ``shared_prompts/`` + one agent with ``prompt.md``."""
    root = tmp_path
    shared = root / "shared_prompts"
    shared.mkdir()
    (shared / "identity.md").write_text("# identity-block\n", encoding="utf-8")
    (shared / "files.md").write_text("# files-block\n", encoding="utf-8")
    agent = root / "fixture_agent"
    agent.mkdir()
    (agent / "prompt.md").write_text("# agent-block\n", encoding="utf-8")
    monkeypatch.setattr(pu, "agents_root", lambda: root)
    return root


def test_agents_root_is_internal_agents_package() -> None:
    assert pu.agents_root().name == "agents"
    assert (pu.agents_root() / "shared_prompts").is_dir()


def test_shared_prompt_mapping_order_in_compose(isolated_agents_root: Path) -> None:
    text = pu.compose_system_prompt("fixture_agent")
    a = text.index("# identity-block")
    b = text.index("# files-block")
    c = text.index("# agent-block")
    assert a < b < c


def test_load_shared_prompt_sections_order(isolated_agents_root: Path) -> None:
    text = pu.load_shared_prompt_sections()
    i = text.index("# identity-block")
    f = text.index("# files-block")
    assert i < f


def test_load_shared_prompt_sections_missing_file_raises(
    isolated_agents_root: Path,
) -> None:
    (isolated_agents_root / "shared_prompts" / "files.md").unlink()
    with pytest.raises(FileNotFoundError):
        pu.load_shared_prompt_sections()


def test_load_agent_prompt_missing_raises(isolated_agents_root: Path) -> None:
    (isolated_agents_root / "fixture_agent" / "prompt.md").unlink()
    with pytest.raises(FileNotFoundError):
        pu.load_agent_prompt("fixture_agent")


def test_ensure_agent_prompt_file_creates_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    shared = root / "shared_prompts"
    shared.mkdir()
    (shared / "identity.md").write_text("i", encoding="utf-8")
    (shared / "files.md").write_text("f", encoding="utf-8")
    monkeypatch.setattr(pu, "agents_root", lambda: root)
    path = pu.ensure_agent_prompt_file("new_agent")
    assert path.name == "prompt.md"
    assert path.read_text(encoding="utf-8").startswith("# new_agent")


def test_inject_system_prompt_placeholders_replaces_date() -> None:
    out = pu.inject_system_prompt_placeholders("Today is {current_date}.")
    assert "{current_date}" not in out
    assert "Today is " in out


def test_format_tool_result_dict() -> None:
    out = pu.format_tool_result("t", "q", {"a": 1})
    assert "Tool: t" in out
    assert "Tool Query: q" in out
    assert '"a"' in out


def test_format_tool_result_str() -> None:
    out = pu.format_tool_result("t", "q", "plain")
    assert "plain" in out


def test_append_file_to_prompt_appends_block() -> None:
    out = pu.append_file_to_prompt("hello", Path("/tmp/x.py"), "line1")
    assert out.startswith("hello\n\n")
    assert "x.py" in out
    assert "line1" in out


def test_format_file_attachment_shape() -> None:
    out = pu.format_file_attachment("a.txt", "body")
    assert "Filename: a.txt" in out
    assert "body" in out
    assert "BEGIN FILE CONTENTS" in out
