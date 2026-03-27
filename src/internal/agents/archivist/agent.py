from thoughtflow import AGENT

from src.internal.agents.prompt_utils import compose_system_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

SELENE_SYSTEM_PROMPT = compose_system_prompt("archivist")

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

tools = get_tool_list("archivist")

archivist_agent = AGENT(
    llm=llm,
    system_prompt=SELENE_SYSTEM_PROMPT,
    tools=tools,
    name="archivist",
    max_iterations=5,
)
