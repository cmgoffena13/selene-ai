from thoughtflow.agents import PlanActAgent

from src.internal.agents.prompt_utils import compose_system_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

SELENE_SYSTEM_PROMPT = compose_system_prompt("planner")

planner_agent = PlanActAgent(
    system_prompt=SELENE_SYSTEM_PROMPT,
    llm=llm,
    name="planner",
    max_iterations=5,
)
