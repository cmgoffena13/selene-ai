import structlog
from pydantic import ValidationError
from thoughtflow import AGENT, MEMORY

from src.internal.agents.prompt_utils import (
    extract_tool_result_payload,
    load_agent_prompt,
)
from src.internal.agents.researcher.schema import (
    WebSearchToolResult,
    web_search_tool_result_json_schema,
)
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)

_MAX_TOOL_PARSE_ATTEMPTS = 5


class ResearcherAgent(AGENT):
    def __init__(self):
        self.name = "researcher"
        self.llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
        self.memory = MEMORY()
        self.system_prompt = load_agent_prompt("researcher")
        self.tools = get_tool_list("researcher")
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

    def _extract_prompt(self, memory) -> str:
        msg = memory.last_user_msg()
        return msg.get("content", "")

    def __call__(self, memory) -> MEMORY:
        prompt = self._extract_prompt(memory)
        self.memory.add_msg("user", prompt)

        for attempt in range(_MAX_TOOL_PARSE_ATTEMPTS):
            try:
                self.memory = super().__call__(self.memory)
                result = self._payload_for_validation(self.memory)
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
                    "Your previous reply was not valid JSON matching the schema, or "
                    f"failed validation: {last_err}\n\n"
                    "You MUST call the web search tool and return the results in the correct format."
                    "Reply with a single JSON object only, no markdown"
                )
                self.memory.add_msg("assistant", result)
                self.memory.add_msg("user", feedback)

        out = self._payload_for_validation(self.memory)
        self.memory.add_msg("assistant", out)
        logger.debug("ResearcherAgent Output", output=out)
        return self.memory
