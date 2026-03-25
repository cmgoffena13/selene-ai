from abc import ABC, abstractmethod
from typing import Dict

from thoughtflow import AGENT

from src.internal.agents.planact.agent import planact_agent
from src.internal.agents.react.agent import react_agent
from src.internal.agents.reflect.agent import reflect_agent


class AgentFactory(ABC):
    _registry: Dict[str, AGENT] = {
        "planact": planact_agent,
        "react": react_agent,
        "reflect": reflect_agent,
    }

    @abstractmethod
    def create_agent(self, agent_name: str) -> AGENT:
        if agent_name not in self._registry:
            raise ValueError(
                f"Agent {agent_name} not found, available agents: {list(self._registry.keys())}"
            )
        return self._registry[agent_name]
