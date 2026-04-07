import structlog
from pydantic import ValidationError
from thoughtflow import AGENT, MEMORY

from src.internal.agents.prompt_utils import (
    apply_planner_agent_hint,
    load_agent_prompt,
    specialist_tool_payload_text,
)
from src.internal.agents.researcher.schema import WebSearchToolResult
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)

_MAX_TOOL_PARSE_ATTEMPTS = 5


RESEARCHER_LLM_OPTIONS = {
    "num_ctx": 256,  # Minimal context needed
    "temperature": 0.0,  # Always deterministic
    "top_p": 0.8,  # Narrow sampling
    "top_k": 20,  # Fewer token choices
    "repeat_penalty": 1.0,  # No penalty needed
    "num_thread": 4,  # Light CPU load
    "num_gpu": 99,  # Full GPU offload
}


class ResearcherAgent(AGENT):
    def __init__(self, *, agent_hint: str | None = None):
        self.name = "researcher"
        self.llm = get_ollama_llm(
            config.SELENE_OLLAMA_MODEL, options=RESEARCHER_LLM_OPTIONS, think=False
        )
        self.memory = MEMORY()
        self.system_prompt = apply_planner_agent_hint(
            load_agent_prompt("researcher"), agent_hint
        )
        self.tools = get_tool_list("researcher")
        self.max_iterations = 1
        super().__init__(
            name=self.name,
            llm=self.llm,
            system_prompt=self.system_prompt,
            tools=self.tools,
            max_iterations=self.max_iterations,
        )

    def __call__(self, memory) -> MEMORY:
        prompt = memory.last_user_msg(content_only=True)
        self.memory.add_msg("user", prompt)

        for attempt in range(_MAX_TOOL_PARSE_ATTEMPTS):
            try:
                self.memory = super().__call__(self.memory)
                result = specialist_tool_payload_text(self.memory)
                logger.debug("ResearcherAgent Output", output=result)
                WebSearchToolResult.model_validate_json(result)
                return self.memory
            except ValidationError as e:
                last_err = str(e)
                logger.warning(
                    "ResearcherAgent validation failed",
                    attempt=attempt + 1,
                    error=last_err,
                )
                if attempt >= _MAX_TOOL_PARSE_ATTEMPTS - 1:
                    break
                feedback = (
                    "Either the web_search tool did not run, or its result did not validate.\n"
                    f"Details: {last_err}\n\n"
                    "To invoke the tool, your assistant reply must be tool-call JSON only, e.g. "
                    '{"name":"web_search","arguments":{"query":"...","topic":"news","time_range":"week"}} '
                    "(not a flat {query,topic,time_range} object, and not invented search results). "
                    "No markdown, no prose."
                )
                self.memory.add_msg("assistant", result)
                self.memory.add_msg("user", feedback)

        out = specialist_tool_payload_text(self.memory)
        self.memory.add_msg("assistant", out)
        logger.debug("ResearcherAgent Output", output=out)
        return self.memory
