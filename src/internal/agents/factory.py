from abc import ABC
from typing import Callable, Dict

from thoughtflow import AGENT

from src.internal.agents.archivist.agent import ArchivistAgent
from src.internal.agents.researcher.agent import ResearcherAgent
from src.settings import is_archivist_configured, is_researcher_configured


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
    def get_agent_names(cls) -> tuple[str, ...]:
        names: list[str] = []
        if is_researcher_configured():
            names.append("researcher")
        if is_archivist_configured():
            names.append("archivist")
        names.append("general")
        return tuple(names)

    @classmethod
    def create_agent(cls, agent_name: str, *, agent_hint: str | None = None) -> AGENT:
        if agent_name not in cls._registry:
            raise ValueError(
                f"Agent {agent_name!r} not in registry; known: {tuple(cls._registry)}"
            )
        return cls._registry[agent_name](agent_hint=agent_hint)
