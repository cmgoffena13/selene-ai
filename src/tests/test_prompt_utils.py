from collections.abc import Callable
from pathlib import Path

import pytest

from src.exceptions import AgentDoesNotExistError
from src.internal.agents import prompt_utils as pu


def test_agent_prompts_dir_ends_with_agent_prompts() -> None:
    p = pu.agent_prompts_dir("general")
    assert p.name == "prompts"
    assert p.parent.name == "general"


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


def test_list_agent_prompt_files_general_includes_mapped_prompts() -> None:
    paths = pu.list_agent_prompt_files("general")
    names = {p.name for p in paths}
    assert "identity.md" in names
    assert "tools.md" in names


def test_list_agent_prompt_files_missing_agent() -> None:
    with pytest.raises(AgentDoesNotExistError):
        pu.list_agent_prompt_files("__no_such_agent__")


def test_build_system_prompt_concatenates_in_mapping_order(
    monkeypatch: pytest.MonkeyPatch,
    patch_agent_prompts_dir: Callable[[str, Path], None],
    prompt_agents_fixtures_dir: Path,
) -> None:
    monkeypatch.setattr(
        pu,
        "PROMPT_MAPPING",
        {"system.md": 1, "tools.md": 2, "files.md": 3},
    )
    prompts = prompt_agents_fixtures_dir / "complete" / "prompts"
    patch_agent_prompts_dir("fixture_agent", prompts)
    text = pu.build_system_prompt("fixture_agent")
    a = text.index("# system fixture chunk")
    b = text.index("# tools fixture chunk")
    c = text.index("# files fixture chunk")
    assert a < b < c


def test_build_system_prompt_skips_missing_mapped_files(
    monkeypatch: pytest.MonkeyPatch,
    patch_agent_prompts_dir: Callable[[str, Path], None],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        pu,
        "PROMPT_MAPPING",
        {"system.md": 1, "tools.md": 2, "files.md": 3},
    )
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "system.md").write_text("only_system", encoding="utf-8")
    patch_agent_prompts_dir("fixture_agent", prompts)
    assert pu.build_system_prompt("fixture_agent") == "only_system"


def test_build_system_prompt_ignores_unmapped_nested_file(
    monkeypatch: pytest.MonkeyPatch,
    patch_agent_prompts_dir: Callable[[str, Path], None],
    prompt_agents_fixtures_dir: Path,
) -> None:
    monkeypatch.setattr(
        pu,
        "PROMPT_MAPPING",
        {"system.md": 1, "tools.md": 2, "files.md": 3},
    )
    prompts = prompt_agents_fixtures_dir / "with_nested" / "prompts"
    patch_agent_prompts_dir("fixture_agent", prompts)
    text = pu.build_system_prompt("fixture_agent")
    assert "ignored by build_system_prompt" not in text
    assert "nested-fixture-system" in text


def test_list_agent_prompt_files_includes_nested_and_paths_sorted(
    patch_agent_prompts_dir: Callable[[str, Path], None],
    prompt_agents_fixtures_dir: Path,
) -> None:
    prompts = prompt_agents_fixtures_dir / "with_nested" / "prompts"
    patch_agent_prompts_dir("fixture_agent", prompts)
    paths = pu.list_agent_prompt_files("fixture_agent")
    assert paths == sorted(paths)
    names = {p.name for p in paths}
    assert "extra.md" in names
    assert "system.md" in names


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
