from thoughtflow import TOOL

from src.internal.tools.local_search import get_local_search_tool
from src.internal.tools.web_search import get_web_search_tool


def get_tool_list(agent_name: str) -> list[TOOL]:
    tool_list: list[TOOL] = []

    local_search = get_local_search_tool()
    if local_search is not None and agent_name == "archivist":
        tool_list.append(local_search)

    web_search = get_web_search_tool()
    if web_search is not None and agent_name == "researcher":
        tool_list.append(web_search)

    return tool_list
