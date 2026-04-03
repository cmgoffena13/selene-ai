import json
from typing import Dict

import structlog
from thoughtflow import AGENT, MEMORY

from src.internal.agents.factory import AgentFactory
from src.internal.agents.planner.agent import PlannerAgent
from src.internal.agents.planner.schema import RoutingPlan, planner_json_schema
from src.internal.agents.prompt_utils import (
    apply_planner_agent_hint,
    extract_tool_result_payload,
    load_agent_prompt,
)
from src.internal.llm.ollama import get_ollama_llm
from src.settings import config

logger = structlog.getLogger(__name__)


class OrchestratorAgent(AGENT):
    def __init__(self):
        self.name = "selene"
        self.llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
        self.system_prompt = load_agent_prompt("orchestrator")
        self.max_iterations = 1
        super().__init__(
            name=self.name,
            llm=self.llm,
            system_prompt=self.system_prompt,
            max_iterations=self.max_iterations,
        )
        self.planner_llm = get_ollama_llm(
            config.SELENE_OLLAMA_MODEL, format=planner_json_schema()
        )
        self.planner_agent = PlannerAgent(
            system_prompt=load_agent_prompt("planner"),
            llm=self.planner_llm,
            name="planner",
            max_iterations=2,
        )

    def _sub_agent_result_text(self, mem: MEMORY) -> str:
        """
        Prefer the last tool ``result`` payload (ThoughtFlow wraps tool output in JSON).
        """
        inner = extract_tool_result_payload(mem)
        if inner is not None:
            return inner
        else:
            return "Result not found."

    def __call__(self, memory):
        prompt = memory.last_user_msg(content_only=True)
        if not prompt:
            logger.warning("No prompt found to respond to.")
            memory.add_msg("assistant", "No prompt found to respond to.")
            return memory

        logger.info("User Asked Selene a Question", prompt=prompt)
        plan: RoutingPlan = self.planner_agent(memory)

        if not plan.agent or plan.agent == "general":
            main_system_prompt = self.system_prompt
            self.system_prompt = apply_planner_agent_hint(
                main_system_prompt, plan.agent_hint
            )
            try:
                return super().__call__(memory)
            finally:
                self.system_prompt = main_system_prompt

        routed_agent = AgentFactory.create_agent(plan.agent, agent_hint=plan.agent_hint)
        routed_agent_memory = MEMORY()
        routed_agent_memory.add_msg("user", prompt)
        routed_agent_memory = routed_agent(routed_agent_memory)
        routed_agent_result = self._sub_agent_result_text(routed_agent_memory)

        synthesis_system = json.dumps(
            {"specialist": plan.agent, "result": routed_agent_result}
        )
        logger.info(
            "OrchestratorAgent Synthesis Input",
            user_prompt=prompt,
            specialist=plan.agent,
            synthesis_system_chars=len(synthesis_system),
        )

        memory.add_msg("system", synthesis_system)
        memory = super().__call__(memory)
        return memory


orchestrator_agent = OrchestratorAgent()
