from thoughtflow.agents import ReactAgent

from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

react_agent = ReactAgent(
    llm=llm,
    name="react",
    max_iterations=5,
)
