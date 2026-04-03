from typing import Any

import structlog
from pydantic import ValidationError
from thoughtflow import AGENT

from src.internal.agents.factory import AgentFactory
from src.internal.agents.planner.schema import RoutingPlan

logger = structlog.getLogger(__name__)

_MAX_PLAN_ATTEMPTS = 3


class PlannerAgent(AGENT):
    """Plans which sub-agent should handle the user turn; JSON in/out via Ollama ``format``."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_list = AgentFactory.get_agent_names()
        self.system_prompt = self.system_prompt.replace(
            "{{agent_list}}", str(self.agent_list)
        )

    def _extract_prompt(self, memory) -> str:
        return memory.last_user_msg(content_only=True)

    def _parse_routing_plan(self, raw: str) -> RoutingPlan:
        text = (raw or "").strip()
        return RoutingPlan.model_validate_json(text)

    def generate_agent_route(self, input_prompt: str) -> RoutingPlan:
        """
        Return a validated routing plan (agent, optional rationale and ``agent_hint``).

        Calls the planner LLM up to :data:`_MAX_PLAN_ATTEMPTS` times with validation
        feedback on parse/validation failure. On exhaustion, returns ``general`` with
        no hint.
        """
        llm = self.llm
        if llm is None:
            raise RuntimeError("PlannerAgent requires llm")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_prompt},
        ]

        last_raw = ""
        last_err: str | None = None

        for attempt in range(_MAX_PLAN_ATTEMPTS):
            result = llm.call(messages)
            last_raw = (result[0] if result else "") or ""
            logger.info("PlannerAgent Output", attempt=attempt + 1, raw=last_raw)

            try:
                plan = self._parse_routing_plan(last_raw)
                return plan
            except ValidationError as e:
                last_err = str(e)
                logger.warning(
                    "PlannerAgent validation failed",
                    attempt=attempt + 1,
                    error=last_err,
                )
                if attempt >= _MAX_PLAN_ATTEMPTS - 1:
                    break
                feedback = (
                    "Your previous reply was not valid JSON matching the schema, or "
                    f"failed validation: {last_err}\n\n"
                    "Reply with a single JSON object only, no markdown, with fields "
                    "`agent` (one of the allowed names), optional `rationale`, and "
                    "optional `agent_hint` (guidance for the specialist)."
                )
                messages.append({"role": "assistant", "content": last_raw})
                messages.append({"role": "user", "content": feedback})

        logger.error(
            "PlannerAgent exhausted retries; falling back to general",
            last_error=last_err,
        )
        return RoutingPlan(agent="general", rationale=None, agent_hint=None)
