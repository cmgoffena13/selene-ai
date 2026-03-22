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


def test_list_agent_prompt_files_general_includes_system_md() -> None:
    paths = pu.list_agent_prompt_files("general")
    names = {p.name for p in paths}
    assert "system.md" in names


def test_list_agent_prompt_files_missing_agent() -> None:
    with pytest.raises(AgentDoesNotExistError):
        pu.list_agent_prompt_files("__no_such_agent__")
