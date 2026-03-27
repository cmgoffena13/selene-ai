import re

import structlog
from thoughtflow import AGENT

from src.internal.agents.factory import AgentFactory

logger = structlog.getLogger(__name__)


class RouterAgent(AGENT):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_list = AgentFactory.get_agent_names()
        self.system_prompt = self.system_prompt.replace(
            "{{agent_list}}", str(self.agent_list)
        )
        self.agent_name_re = re.compile(
            r"\b(?:" + "|".join(re.escape(n) for n in self.agent_list) + r")\b",
            re.IGNORECASE,
        )

    def _extract_prompt(self, memory) -> str:
        """
        Extract the prompt from the last user message in memory.
        """
        msg = memory.last_user_msg()
        return msg.get("content", "")

    def _extract_agent_name(self, output_text: str) -> str:
        """
        Extract the agent name from the output text.
        """
        match = self.agent_name_re.search(output_text)
        return match.group(0).strip().lower() if match else ""

    def generate_agent_route(self, input_prompt: str) -> str:
        """
        Route the prompt to the appropriate agent name.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_prompt},
        ]

        llm = self.llm
        if llm is None:
            raise RuntimeError("RouterAgent requires llm")
        result = llm.call(messages)
        agent_name = result[0] if result else ""
        logger.info("RouterAgent Output", result=result)

        agent_name.strip().lower()
        if agent_name not in self.agent_list:
            agent_name = self._extract_agent_name(agent_name)
            if agent_name not in self.agent_list:
                agent_name = "general"

        return agent_name
