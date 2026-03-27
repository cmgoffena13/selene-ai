from thoughtflow import AGENT

from src.internal.agents.prompt_utils import compose_system_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

SELENE_SYSTEM_PROMPT = compose_system_prompt("general")

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

general_agent = AGENT(
    llm=llm,
    system_prompt=SELENE_SYSTEM_PROMPT,
    name="general",
    max_iterations=5,
)
