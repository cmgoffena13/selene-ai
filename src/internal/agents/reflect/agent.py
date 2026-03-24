from thoughtflow.agents import ReflectAgent

from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

reflect_agent = ReflectAgent(
    llm=llm,
    name="reflect",
    max_iterations=5,
)
