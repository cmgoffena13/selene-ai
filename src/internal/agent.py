from thoughtflow import AGENT

from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

SYSTEM_PROMPT = """
You are Selene from the Underworld series. Vampire death dealer. Adopted daughter of Viktor.

You are also a helpful assistant.

Tool use (IMPORTANT):
- You may use web_search at most ONCE per user question.
- If you need current or factual information from the web, call the tool by responding with ONLY valid JSON in this exact shape:
  {"tool_calls":[{"name":"web_search","arguments":{"query":"..."}}]}
- Use the exact key "arguments" (not "parameters").
- Use the exact tool name "web_search".
- After you receive tool results, you MUST answer the user in normal text (no JSON) and MUST NOT call any more tools. If you call a tool again, you are wrong.
"""

llm = get_ollama_llm(config.OLLAMA_MODEL)
tools = get_tool_list()


def _guard_repeated_tools(tool_name: str, arguments: dict) -> bool:
    # Thoughtflow hook: block repeated web_search calls so we don't loop.
    if tool_name == "web_search":
        already_used = getattr(_guard_repeated_tools, "_used_web_search", False)
        if already_used:
            return False
        setattr(_guard_repeated_tools, "_used_web_search", True)
    return True


selene_agent = AGENT(
    llm=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    name="selene",
    max_iterations=6,
    on_tool_call=_guard_repeated_tools,
)
