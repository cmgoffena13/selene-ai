from abc import ABC
from functools import lru_cache
from typing import Dict

from thoughtflow import AGENT

from src.internal.agents.general.agent import general_agent
from src.internal.agents.planner.agent import planner_agent
from src.internal.agents.react.agent import react_agent
from src.internal.agents.reflect.agent import reflect_agent


class AgentFactory(ABC):
    _registry: Dict[str, AGENT] = {
        "planner": planner_agent,
        "react": react_agent,
        "reflect": reflect_agent,
        "general": general_agent,
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
