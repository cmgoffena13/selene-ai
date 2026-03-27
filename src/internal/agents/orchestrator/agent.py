from typing import Dict

import structlog
from thoughtflow import AGENT, MEMORY

from src.internal.agents.factory import AgentFactory
from src.internal.agents.prompt_utils import compose_system_prompt, load_agent_prompt
from src.internal.agents.router.agent import RouterAgent
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

logger = structlog.getLogger(__name__)


class OrchestratorAgent(AGENT):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "selene"
        self.llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
        self.system_prompt = compose_system_prompt("orchestrator")
        self.router_agent = RouterAgent(
            system_prompt=load_agent_prompt("router"),
            llm=self.llm,
            name="router",
            max_iterations=2,
        )
        self.active_sub_agents: Dict[str, AGENT] = {}

    def _extract_prompt(self, memory) -> str:
        """
        Extract the prompt from the last user message in memory.
        """
        msg = memory.last_user_msg()
        return msg.get("content", "")

    def _last_result_or_assistant_content(self, mem: MEMORY) -> str:
        """Prefer the last tool ``result`` message; else last assistant text."""
        result_msgs = mem.get_msgs(include=["result"])
        if result_msgs:
            return str(result_msgs[-1].get("content", "")).lstrip()
        last = mem.last_asst_msg()
        if last is None:
            return "No input from sub agent."
        if isinstance(last, dict):
            return str(last.get("content", "")).lstrip()
        return str(last).lstrip()

    def _generate_user_prompt(self, input_prompt: str, sub_agent_result: str) -> str:
        prompt_template = f"""
        Original User Query: {input_prompt}
        
        Sub Agent Result:
        {sub_agent_result}
        
        Synthesize these into a final coherent response to the original query.
        """
        return prompt_template.strip()

    def __call__(self, memory):
        prompt = self._extract_prompt(memory)
        if not prompt:
            memory.add_msg("assistant", "No prompt found to respond to.")

        routed_agent_name = self.router_agent.generate_agent_route(prompt)

        # NOTE: If the router agent cannot determine an appropriate agent, the orchestrator will respond to the user directly.
        if not routed_agent_name or routed_agent_name == "general":
            return super().__call__(memory)

        routed_agent = AgentFactory.create_agent(routed_agent_name)
        routed_agent_memory = MEMORY()
        routed_agent_memory.add_msg("user", prompt)
        routed_agent_memory = routed_agent(routed_agent_memory)

        routed_agent_result = self._last_result_or_assistant_content(
            routed_agent_memory
        )
        memory.add_msg("assistant", routed_agent_result)

        # NOTE: This is the prompt that the orchestrator will use to respond to the user.
        user_prompt = self._generate_user_prompt(prompt, routed_agent_result)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        logger.debug("User Prompt Constructed", user_prompt=user_prompt)

        llm = self.llm
        if llm is None:
            raise RuntimeError("OrchestratorAgent requires an llm")
        result = llm.call(messages)
        memory.add_msg("assistant", result[0] or "")

        return memory


orchestrator_agent = OrchestratorAgent()
