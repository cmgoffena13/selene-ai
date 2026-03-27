import structlog
from thoughtflow import AGENT, MEMORY

from src.internal.agents.prompt_utils import load_agent_prompt
from src.internal.llm.ollama import get_ollama_llm
from src.internal.tools.registry import get_tool_list
from src.settings import config

logger = structlog.getLogger(__name__)


class ArchivistAgent(AGENT):
    def __init__(self):
        self.name = "archivist"
        self.llm = get_ollama_llm(config.SELENE_OLLAMA_MODEL)
        self.memory = MEMORY()
        self.system_prompt = load_agent_prompt("archivist")
        self.tools = get_tool_list("archivist")
        self.max_iterations = 1
        super().__init__(
            name=self.name,
            llm=self.llm,
            system_prompt=self.system_prompt,
            tools=self.tools,
            max_iterations=self.max_iterations,
        )

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

    def _extract_prompt(self, memory) -> str:
        """
        Extract the prompt from the last user message in memory.
        """
        msg = memory.last_user_msg()
        return msg.get("content", "")

    def __call__(self, memory) -> MEMORY:
        prompt = self._extract_prompt(memory)
        self.memory.add_msg("user", prompt)
        self.memory = super().__call__(self.memory)
        result = self._last_result_or_assistant_content(self.memory)
        logger.debug("ArchivistAgent Output", output=result)
        return self.memory
