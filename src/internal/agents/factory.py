from abc import ABC
from functools import lru_cache
from typing import Dict, Type

from thoughtflow import AGENT

from src.internal.agents.archivist.agent import ArchivistAgent
from src.internal.agents.researcher.agent import ResearcherAgent


class AgentFactory(ABC):
    _registry: Dict[str, Type[AGENT]] = {
        "researcher": ResearcherAgent,
        "archivist": ArchivistAgent,
    }

    @classmethod
    @lru_cache(maxsize=1)
    def get_agent_names(cls) -> tuple[str, ...]:
        return (*cls._registry.keys(), "general")

    @classmethod
    def create_agent(cls, agent_name: str) -> AGENT:
        if agent_name not in cls._registry:
            raise ValueError(
                f"Agent {agent_name} not found, available agents: {cls.get_agent_names()}"
            )
        return cls._registry[agent_name]()
