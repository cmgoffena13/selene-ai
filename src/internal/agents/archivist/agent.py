import structlog
from pydantic import ValidationError
from thoughtflow import AGENT, MEMORY

from src.internal.agents.archivist.schema import (
    LocalSearchToolResult,
    local_search_tool_result_json_schema,
)
from src.internal.agents.prompt_utils import (
    apply_planner_agent_hint,
    extract_tool_result_payload,
    load_agent_prompt,
)
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)

_MAX_TOOL_PARSE_ATTEMPTS = 5


ARCHIVIST_LLM_OPTIONS = {
    "num_ctx": 256,  # Minimal context needed
    "temperature": 0.0,  # Always deterministic
    "top_p": 0.8,  # Narrow sampling
    "top_k": 20,  # Fewer token choices
    "repeat_penalty": 1.0,  # No penalty needed
    "num_thread": 4,  # Light CPU load
    "num_gpu": 99,  # Full GPU offload
}


class ArchivistAgent(AGENT):
    def __init__(self, *, agent_hint: str | None = None):
        self.name = "archivist"
        self.llm = get_ollama_llm(
            config.SELENE_OLLAMA_MODEL,
            format=local_search_tool_result_json_schema(),
            options=ARCHIVIST_LLM_OPTIONS,
            think=False,
        )
        self.memory = MEMORY()
        self.system_prompt = apply_planner_agent_hint(
            load_agent_prompt("archivist"), agent_hint
        )
        self.tools = get_tool_list("archivist")
        self.max_iterations = 1
        super().__init__(
            name=self.name,
            llm=self.llm,
            system_prompt=self.system_prompt,
            tools=self.tools,
            max_iterations=self.max_iterations,
        )

    def _payload_for_validation(self, mem: MEMORY) -> str:
        inner = extract_tool_result_payload(mem)
        if inner is not None:
            return inner
        last = mem.last_asst_msg(content_only=True)
        if not last:
            return "No input from sub agent."
        return last.lstrip()

    def __call__(self, memory) -> MEMORY:
        prompt = memory.last_user_msg(content_only=True)
        self.memory.add_msg("user", prompt)

        for attempt in range(_MAX_TOOL_PARSE_ATTEMPTS):
            try:
                self.memory = super().__call__(self.memory)
                result = self._payload_for_validation(self.memory)
                logger.debug("ArchivistAgent Output", output=result)
                LocalSearchToolResult.model_validate_json(result)
                return self.memory
            except ValidationError as e:
                last_err = str(e)
                logger.warning(
                    "ArchivistAgent validation failed",
                    attempt=attempt + 1,
                    error=last_err,
                )
                if attempt >= _MAX_TOOL_PARSE_ATTEMPTS - 1:
                    break
                feedback = (
                    "Your previous reply was not valid JSON matching the schema, or "
                    f"failed validation: {last_err}\n\n"
                    "You MUST call the local search tool and return the results in the correct format."
                    "Reply with a single JSON object only, no markdown"
                )
                self.memory.add_msg("assistant", result)
                self.memory.add_msg("user", feedback)

        out = self._payload_for_validation(self.memory)
        self.memory.add_msg("assistant", out)
        logger.debug("ArchivistAgent Output", output=out)
        return self.memory
