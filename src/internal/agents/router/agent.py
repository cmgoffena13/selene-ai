import re

import structlog
from thoughtflow import AGENT, MEMORY

from src.internal.agents.factory import AgentFactory
from src.internal.agents.prompt_utils import compose_system_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

logger = structlog.getLogger(__name__)


class RouterAgent(AGENT):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_list = AgentFactory.get_agent_names()
        self.agent_lines = "\n".join(f"- {name}" for name in self.agent_list)
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

    def _generate_route(self, input_prompt: str) -> str:
        """
        Route the prompt to the appropriate agent name.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_prompt},
        ]

        llm = self.llm
        if llm is None:
            raise RuntimeError("RouterAgent requires an llm")
        result = llm.call(messages)
        agent_name = result[0] if result else ""
        logger.debug("RouterAgent Output", result=result)

        agent_name.strip().lower()
        if agent_name not in self.agent_list:
            agent_name = self._extract_agent_name(agent_name)
            if agent_name not in self.agent_list:
                agent_name = "general"

        return agent_name

    def __call__(self, memory):
        prompt = self._extract_prompt(memory)

        if not prompt:
            memory.add_msg("assistant", "No prompt found to route.")
            return memory

        agent_name = self._generate_route(prompt)

        memory.add_msg("assistant", f'Routing to "{agent_name}" agent…')

        routed_agent = AgentFactory.create_agent(agent_name)

        # NOTE: After routing, create new memory to isolate agent context
        routed_memory = MEMORY()
        routed_memory.add_msg("user", prompt)
        routed_memory = routed_agent(routed_memory)

        # NOTE: Add logs from the routed agent to the original memory for initial observibility
        routed_logs = routed_memory.get_logs()
        for log in routed_logs:
            memory.add_log(log)

        # NOTE: Add response from the routed agent to the original memory for output
        last_asst_msg = routed_memory.last_asst_msg()
        asst_msg_content = last_asst_msg["content"] if last_asst_msg else ""
        memory.add_msg("assistant", asst_msg_content)

        return memory


llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
SELENE_SYSTEM_PROMPT = compose_system_prompt("router")

router_agent = RouterAgent(
    system_prompt=SELENE_SYSTEM_PROMPT,
    llm=llm,
    name="router",
    max_iterations=5,
)
