from thoughtflow import AGENT

from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

SYSTEM_PROMPT = """
You are Selene from the Underworld series. Vampire death dealer. Adopted daughter of Viktor.

You are also a helpful assistant.
"""

llm = get_ollama_llm(config.OLLAMA_MODEL)
tools = get_tool_list()


selene_agent = AGENT(
    llm=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    name="selene",
    max_iterations=5,
)
