import json
import re

import structlog
from thoughtflow.agents import PlanActAgent

from src.internal.agents.prompt_utils import (
    agent_task_prompt,
    build_system_prompt,
    inject_system_prompt_placeholders,
)
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger("src.internal.agents.planact.agent")

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
tools = get_tool_list()

SYSTEM_PROMPT_TEMPLATE = build_system_prompt("planact")
SELENE_SYSTEM_PROMPT = inject_system_prompt_placeholders(SYSTEM_PROMPT_TEMPLATE)

TASK_PROMPT = agent_task_prompt("planact")

planact_agent = PlanActAgent(
    plan_prompt=TASK_PROMPT,
    system_prompt=SELENE_SYSTEM_PROMPT,
    llm=llm,
    name="planact",
    tools=tools,
    max_iterations=5,
)
