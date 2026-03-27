from thoughtflow.agents import ReactAgent

from src.internal.agents.prompt_utils import compose_system_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)

SELENE_SYSTEM_PROMPT = compose_system_prompt("react")

react_agent = ReactAgent(
    llm=llm,
    system_prompt=SELENE_SYSTEM_PROMPT,
    name="react",
    max_iterations=5,
)
