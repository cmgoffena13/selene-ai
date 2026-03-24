from thoughtflow.agents import PlanActAgent

from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

planact_agent = PlanActAgent(
    llm=llm,
    name="planact",
    max_iterations=5,
)
