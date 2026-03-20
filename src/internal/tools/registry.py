from thoughtflow import TOOL

from src.internal.tools.local_search import get_local_search_tool
from src.internal.tools.web_search import get_web_search_tool


def get_tool_list() -> list[TOOL]:
    tool_list: list[TOOL] = []

    if get_local_search_tool() is not None:
        tool_list.append(get_local_search_tool())

    if get_web_search_tool() is not None:
        tool_list.append(get_web_search_tool())

    return tool_list
