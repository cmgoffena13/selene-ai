import structlog
from thoughtflow import AGENT

from src.internal.agents.prompt_utils import compose_system_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)

SELENE_SYSTEM_PROMPT = compose_system_prompt("general")

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
tools = get_tool_list()

general_agent = AGENT(
    llm=llm,
    tools=tools,
    system_prompt=SELENE_SYSTEM_PROMPT,
    name="selene",
    max_iterations=5,
)
