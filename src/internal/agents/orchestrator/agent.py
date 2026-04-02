import json
from typing import Dict

import structlog
from thoughtflow import AGENT, MEMORY

from src.internal.agents.factory import AgentFactory
from src.internal.agents.planner.agent import PlannerAgent
from src.internal.agents.planner.schema import RoutingPlan, planner_json_schema
from src.internal.agents.prompt_utils import (
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

    def _sub_agent_result_text(self, mem: MEMORY) -> str:
        """
        Prefer the last tool ``result`` payload (ThoughtFlow wraps tool output in JSON).

        If we only used ``last_asst_msg``, we would miss tool-only turns and could pick
        a later assistant apology instead of the structured search/RAG JSON.
        """
        inner = extract_tool_result_payload(mem)
        if inner is not None:
            return inner
        last = mem.last_asst_msg(content_only=True)
        if not last:
            return "No input from sub agent."
        return last.lstrip()

    def _generate_user_prompt(
        self, input_prompt: str, sub_agent_result: str, specialist_name: str
    ) -> str:
        envelope = json.dumps(
            {"name": specialist_name, "result": sub_agent_result},
            ensure_ascii=False,
        )
        return (
            f"Original User Query: {input_prompt}\n\n"
            "Sub Agent Result:\n"
            f"`{envelope}`\n\n"
            "Synthesize these into a final coherent response to the original query."
        )

    def __call__(self, memory):
        prompt = self._extract_prompt(memory)
        if not prompt:
            logger.warning("No prompt found to respond to.")
            memory.add_msg("assistant", "No prompt found to respond to.")
            return memory

        logger.info("User Asked Selene a Question", prompt=prompt)
        plan: RoutingPlan = self.planner_agent.generate_agent_route(prompt)

        # NOTE: If the planner chooses general or fails, the orchestrator answers directly.
        if not plan.agent or plan.agent == "general":
            return super().__call__(memory)

        routed_agent = AgentFactory.create_agent(plan.agent, agent_hint=plan.agent_hint)
        routed_agent_memory = MEMORY()
        routed_agent_memory.add_msg("user", prompt)
        routed_agent_memory = routed_agent(routed_agent_memory)

        routed_agent_result = self._sub_agent_result_text(routed_agent_memory)

        # Sub-agent JSON is only passed into the synthesis call below — do not add it as an
        # assistant turn or the UI will show the raw paste before/with the real answer.
        user_prompt = self._generate_user_prompt(
            prompt, routed_agent_result, plan.agent
        )
        logger.debug("OrchestratorAgent User Prompt", user_prompt=user_prompt)

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
        return memory


orchestrator_agent = OrchestratorAgent()
