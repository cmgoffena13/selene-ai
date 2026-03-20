from pathlib import Path

import structlog
from thoughtflow import AGENT

from src.internal.llm.ollama import get_ollama_llm
from src.internal.prompt_utils import inject_system_prompt_placeholders
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"
_SYSTEM_PROMPT_TEMPLATE = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
SELENE_SYSTEM_PROMPT = inject_system_prompt_placeholders(_SYSTEM_PROMPT_TEMPLATE)

llm = get_ollama_llm(config.OLLAMA_MODEL)
tools = get_tool_list()


selene_agent = AGENT(
    llm=llm,
    tools=tools,
    system_prompt=SELENE_SYSTEM_PROMPT,
    name="selene",
    max_iterations=5,
)
