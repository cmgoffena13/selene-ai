import structlog
from thoughtflow import AGENT

from src.internal.llm.ollama import get_ollama_llm
from src.internal.system import SELENE_SYSTEM_PROMPT
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)

llm = get_ollama_llm(config.OLLAMA_MODEL)
tools = get_tool_list()


selene_agent = AGENT(
    llm=llm,
    tools=tools,
    system_prompt=SELENE_SYSTEM_PROMPT,
    name="selene",
    max_iterations=5,
)
