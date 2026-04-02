from typing import Dict

import structlog
from thoughtflow import AGENT, MEMORY

from src.internal.agents.factory import AgentFactory
from src.internal.agents.planner.agent import PlannerAgent
from src.internal.agents.planner.schema import planner_json_schema
from src.internal.agents.prompt_utils import load_agent_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

logger = structlog.getLogger(__name__)


class OrchestratorAgent(AGENT):
    def __init__(self):
        self.name = "selene"
        self.llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
        self.system_prompt = load_agent_prompt("orchestrator")
        super().__init__(
            name=self.name,
            llm=self.llm,
            system_prompt=self.system_prompt,
        )
        self.planner_llm = get_ollama_llm(
            config.SELENE_OLLAMA_MODEL,
            format=planner_json_schema(),
        )
        self.planner_agent = PlannerAgent(
            system_prompt=load_agent_prompt("planner"),
            llm=self.planner_llm,
            name="planner",
            max_iterations=2,
        )
        self.active_sub_agents: Dict[str, AGENT] = {}

    def _extract_prompt(self, memory) -> str:
        """
        Extract the prompt from the last user message in memory.
        """
        msg = memory.last_user_msg()
        return msg.get("content", "")

    def _last_assistant_content(self, mem: MEMORY) -> str:
        """Last assistant message from routed sub-agent memory (validated tool JSON or prose)."""
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
            logger.warning("No prompt found to respond to.")
            memory.add_msg("assistant", "No prompt found to respond to.")
            return memory

        logger.info("User Asked Selene a Question", prompt=prompt)
        routed_agent_name = self.planner_agent.generate_agent_route(prompt)

        # NOTE: If the planner chooses general or fails, the orchestrator answers directly.
        if not routed_agent_name or routed_agent_name == "general":
            return super().__call__(memory)

        routed_agent = AgentFactory.create_agent(routed_agent_name)
        routed_agent_memory = MEMORY()
        routed_agent_memory.add_msg("user", prompt)
        routed_agent_memory = routed_agent(routed_agent_memory)

        routed_agent_result = self._last_assistant_content(routed_agent_memory)
        memory.add_msg("assistant", routed_agent_result)

        # NOTE: This is the prompt that the orchestrator will use to respond to the user.
        user_prompt = self._generate_user_prompt(prompt, routed_agent_result)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        llm = self.llm
        if llm is None:
            raise RuntimeError("OrchestratorAgent requires an llm")
        result = llm.call(messages)
        output = result[0] or ""
        memory.add_msg("assistant", output)
        logger.debug("OrchestratorAgent Output", output=output)
        return memory


orchestrator_agent = OrchestratorAgent()
