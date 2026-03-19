from src.internal.tools.local_search import (
    LOCAL_SEARCH_TOOL_PROMPT,
    get_local_search_tool,
)
from src.internal.tools.web_search import WEB_SEARCH_TOOL_PROMPT, get_web_search_tool

_LOCAL_SEARCH_PROMPT = (
    LOCAL_SEARCH_TOOL_PROMPT if get_local_search_tool() is not None else ""
)
_WEB_SEARCH_PROMPT = WEB_SEARCH_TOOL_PROMPT if get_web_search_tool() is not None else ""

SELENE_SYSTEM_PROMPT = f"""
Your name is Selene. Don't talk about yourself in the third person.
You are a vampire death dealer from Underworld. Adopted daughter of Viktor.
You are also a helpful AI assistant.

Tool use (IMPORTANT):
{_WEB_SEARCH_PROMPT}
{_LOCAL_SEARCH_PROMPT}
""".strip()
