from abc import ABC
from functools import lru_cache
from typing import Callable, Dict

from thoughtflow import AGENT

from src.internal.agents.archivist.agent import ArchivistAgent
from src.internal.agents.researcher.agent import ResearcherAgent


def _make_researcher(*, agent_hint: str | None = None) -> AGENT:
    return ResearcherAgent(agent_hint=agent_hint)


def _make_archivist(*, agent_hint: str | None = None) -> AGENT:
    return ArchivistAgent(agent_hint=agent_hint)


class AgentFactory(ABC):
    _registry: Dict[str, Callable[..., AGENT]] = {
        "researcher": _make_researcher,
        "archivist": _make_archivist,
    }

    @classmethod
    @lru_cache(maxsize=1)
    def get_agent_names(cls) -> tuple[str, ...]:
        return (*cls._registry.keys(), "general")

    @classmethod
    def create_agent(cls, agent_name: str, *, agent_hint: str | None = None) -> AGENT:
        if agent_name not in cls._registry:
            raise ValueError(
                f"Agent {agent_name} not found, available agents: {cls.get_agent_names()}"
            )
        return cls._registry[agent_name](agent_hint=agent_hint)
