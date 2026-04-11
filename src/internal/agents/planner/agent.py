import structlog
from pydantic import ValidationError
from thoughtflow import AGENT

from src.internal.agents.factory import AgentFactory
from src.internal.agents.planner.schema import RoutingPlan

logger = structlog.getLogger(__name__)

_MAX_PLAN_ATTEMPTS = 3
_MAX_ROUTING_CONTEXT_MESSAGES = 4


class PlannerAgent(AGENT):
    """Plans which sub-agent should handle the user turn; JSON in/out via Ollama ``format``."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_list = AgentFactory.get_agent_names()
        self.system_prompt = self.system_prompt.replace(
            "{{agent_list}}", str(self.agent_list)
        )

    def _routing_user_content(self, memory) -> str:
        """
        Build planner user text: latest user turn, plus prior user/assistant turns for context.
        """
        last_user = memory.last_user_msg(content_only=True)

        messages = memory.get_msgs(include=["user", "assistant"], limit=-1)
        if len(messages) > _MAX_ROUTING_CONTEXT_MESSAGES:
            messages = messages[-_MAX_ROUTING_CONTEXT_MESSAGES:]

        lines = []
        for message in messages:
            role = message["role"]
            content = (message.get("content") or "").strip()
            if not content:
                continue
            lines.append(f"{role.upper()}: {content}")

        if len(lines) <= 1:
            return last_user

        transcript = "\n".join(lines)
        return (
            "Conversation context (use this to interpret follow-ups and short questions; "
            "you must still route for the **latest** user message only):\n\n"
            f"{transcript}\n"
        )

    def __call__(self, memory) -> RoutingPlan:
        """
        Return a validated routing plan from conversation ``memory``.

        Uses recent user/assistant messages as context so short follow-ups can be routed
        with reference to prior turns. Does not run the default AGENT tool loop.
        """
        llm = self.llm
        if llm is None:
            raise RuntimeError("PlannerAgent requires llm")

        user_content = self._routing_user_content(memory)
        if not user_content:
            return RoutingPlan(
                specialist="general", rationale=None, specialist_hint=None
            )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

        last_err = None
        for attempt in range(_MAX_PLAN_ATTEMPTS):
            result = llm.call(messages)
            output = result[0].strip() if result else ""
            logger.info("PlannerAgent Output", attempt=attempt + 1, output=output)

            try:
                plan = RoutingPlan.model_validate_json(output)
                return plan
            except ValidationError as e:
                last_err = str(e)
                logger.warning(
                    "PlannerAgent validation failed",
                    attempt=attempt + 1,
                    output=output,
                    error=last_err,
                )
                if attempt >= _MAX_PLAN_ATTEMPTS - 1:
                    break
                feedback = (
                    "Your previous reply was not valid JSON matching the schema, or "
                    f"failed validation: {last_err}\n\n"
                    "Reply with a single JSON object only, no markdown, with fields "
                    "`specialist` (one of the allowed names), optional `rationale`, and "
                    "optional `specialist_hint` (guidance for the specialist)."
                )
                messages.append({"role": "assistant", "content": output})
                messages.append({"role": "user", "content": feedback})

        logger.error(
            "PlannerAgent exhausted retries; falling back to general",
            last_error=last_err,
        )
        return RoutingPlan(specialist="general", rationale=None, specialist_hint=None)
