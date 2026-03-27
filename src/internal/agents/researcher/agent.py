from thoughtflow import AGENT

from src.internal.agents.prompt_utils import load_agent_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

RESEARCHER_SYSTEM_PROMPT = load_agent_prompt("researcher")

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

tools = get_tool_list("researcher")

researcher_agent = AGENT(
    llm=llm,
    system_prompt=RESEARCHER_SYSTEM_PROMPT,
    tools=tools,
    name="researcher",
    max_iterations=5,
)
