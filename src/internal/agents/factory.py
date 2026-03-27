from abc import ABC
from functools import lru_cache
from typing import Dict

from thoughtflow import AGENT

from src.internal.agents.archivist.agent import archivist_agent
from src.internal.agents.researcher.agent import researcher_agent


class AgentFactory(ABC):
    _registry: Dict[str, AGENT] = {
        "researcher": researcher_agent,
        "archivist": archivist_agent,
    }

    @classmethod
    @lru_cache(maxsize=1)
    def get_agent_names(cls) -> tuple[str, ...]:
        return tuple(cls._registry.keys())

    @classmethod
    def create_agent(cls, agent_name: str) -> AGENT:
        if agent_name not in cls._registry:
            raise ValueError(
                f"Agent {agent_name} not found, available agents: {cls.get_agent_names()}"
            )
        return cls._registry[agent_name]
