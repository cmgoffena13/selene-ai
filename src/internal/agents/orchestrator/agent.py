from typing import Dict

import structlog
from thoughtflow import AGENT

from src.internal.agents.prompt_utils import compose_system_prompt, load_agent_prompt
from src.internal.agents.router.agent import RouterAgent
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

logger = structlog.getLogger(__name__)


class OrchestratorAgent(AGENT):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
        self.router_agent = RouterAgent(
            system_prompt=load_agent_prompt("router"),
            llm=self.llm,
            name="router",
            max_iterations=2,
        )
        self.active_sub_agents: Dict[str, AGENT] = {}

    def __call__(self, memory):
        super().__call__(memory)
        return memory


SELENE_SYSTEM_PROMPT = compose_system_prompt("orchestrator")
orchestrator_agent = OrchestratorAgent(
    name="selene", system_prompt=SELENE_SYSTEM_PROMPT
)
