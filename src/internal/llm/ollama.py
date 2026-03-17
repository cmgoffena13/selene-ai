import json
from typing import Any

from thoughtflow import LLM


def get_ollama_llm(model: str) -> LLM:
    """
    Return a thoughtflow LLM that uses Ollama at http://localhost:11434.

    Use with MEMORY, THOUGHT, AGENT, etc. For a different host, pass
    ollama_url in the step's params when calling.
    """

    class _ThoughtflowCompatibleOllamaLLM(LLM):
        """
        Thoughtflow's AGENT detects tool calls by JSON-parsing the assistant text.

        Ollama (when tools are enabled) often returns tool calls in
        response.message.tool_calls while message.content is empty.

        This wrapper surfaces those tool calls as assistant text:
          {"tool_calls":[{"name":"...","arguments":{...}}]}
        so thoughtflow.AGENT can parse and execute them.
        """

        def _normalize_messages(self, msg_list):
            """
            Thoughtflow AGENT writes tool interactions into MEMORY as roles:
            - action: {"tool_call": {...}}
            - result: {"name": "...", "result": "..."}
            Ollama doesn't reliably respond when fed unknown roles, so we map:
            - action -> dropped
            - result -> user message containing the tool result
            """
            base = super()._normalize_messages(msg_list)
            out = []
            for m in base:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "action":
                    continue
                if role == "result":
                    try:
                        data = json.loads(content) if isinstance(content, str) else {}
                    except json.JSONDecodeError:
                        data = {}
                    name = (data.get("name") or "tool").strip()
                    result = data.get("result")
                    if result is None:
                        result = content
                    out.append(
                        {
                            "role": "user",
                            "content": (
                                f"TOOL RESULT ({name}):\n{result}\n\n"
                                "You have the information you requested.\n"
                                "Do NOT call any tools again.\n"
                                "Answer the user now in normal text."
                            ),
                        }
                    )
                    continue
                out.append(m)
            return out

        def _call_ollama(self, msg_list, params):  # type: ignore[override]
            res = super()._send_request(  # reuse base HTTP helper
                (
                    params.get("ollama_url", "http://localhost:11434").rstrip("/")
                    + "/api/chat"
                ),
                json.dumps(
                    {
                        "model": self.model,
                        "messages": self._normalize_messages(msg_list),
                        "stream": False,
                        **{
                            k: v
                            for k, v in params.items()
                            if k not in ("ollama_url", "model")
                        },
                    }
                ).encode("utf-8"),
                {"Content-Type": "application/json"},
            )

            # Prefer OpenAI-style choices if present
            if "choices" in res:
                return [a["message"]["content"] for a in res.get("choices", [])]

            msg = res.get("message") if isinstance(res, dict) else None
            if isinstance(msg, dict):
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    normalized: list[dict[str, Any]] = []
                    for tc in tool_calls:
                        if not isinstance(tc, dict):
                            continue
                        # Ollama commonly uses {"function": {"name": str, "arguments": {...}}}
                        fn = (
                            tc.get("function")
                            if isinstance(tc.get("function"), dict)
                            else None
                        )
                        if fn:
                            name = fn.get("name") or tc.get("name") or ""
                            args = (
                                fn.get("arguments")
                                or fn.get("parameters")
                                or tc.get("arguments")
                                or tc.get("parameters")
                                or {}
                            )
                        else:
                            name = tc.get("name") or ""
                            args = tc.get("arguments") or tc.get("parameters") or {}

                        # Ollama may return arguments as a JSON string
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {"_raw": args}

                        if name:
                            normalized.append({"name": name, "arguments": args or {}})

                    return (
                        [json.dumps({"tool_calls": normalized})]
                        if normalized
                        else [msg.get("content", "")]
                    )

                return [msg.get("content", "")]

            # Fallback
            if isinstance(res, dict) and "response" in res:
                return [res["response"]]
            return [""]

    return _ThoughtflowCompatibleOllamaLLM(f"ollama:{model}", key="")
