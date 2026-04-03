# Standards

This doc holds the format and structure of specific prompt formats & structure throughout Selene.

## File Content

```
Filename: [filename]
File contents:
----- BEGIN FILE CONTENTS -----
[actual file content]
----- END FILE CONTENTS -----
```

Specialist tools return **JSON** strings (validated by Pydantic schemas in each agent’s `schema.py`).

## Notes
An agent's context typically includes:
- System instructions — Who the agent is, how it should behave, what rules to follow
- User instructions — The task description and any clarifications
- Conversation history — Previous messages and actions in the current session
- Tool results — Output from searches, file reads, command executions
- Retrieved documents — Information pulled from RAG systems or knowledge bases

System Prompt Sections?
- Who the AI is
- How they speak / interact
- Set the Knowledge Base (ex. Current Date)
- Dos / Donts (enfore rules)
- What to do (Task Instruction)

Prompt Research:
- General: https://www.promptingguide.ai
- ChatGPT: https://developers.openai.com/api/docs/guides/prompt-engineering
- Claude: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Gemini: https://cloud.google.com/discover/what-is-prompt-engineering?hl=en
- Llama: https://www.llama.com/docs/how-to-guides/prompting/
- Mistral: https://docs.mistral.ai/capabilities/completion/prompting_capabilities

## Tips & Tricks
- Use precise language (adjectives) -- clear and direct
- Provide Context/Motivation behind rules to help
- Provide Example Input/Output
- Use XML tags (Might just be for Claude)
- In regards to context, place long-form docs and inputs near the top (first).
- Tell the model what to do rather than not what to do.
- Quantify the request when possible.
- Breakdown down complex tasks into subtasks (1., 2., 3. etc)
- Test Prompt Variation (keywords, level of detail, prompt length, etc.)
- Remember the PBJ Assignment, every step matters

## Architecture Notes
Need a planner Agent to best support user experience. This planner agent will:
- Analyze Intent, Complexity, and Required Domain Knowledge.
- Analyze input to determine the agent needed
    - Single Domain? Single-step task?
        - Yes -> route to specialist
        - No -> Give plan of specialists with dependencies

AI Thought
```
Here's what that "classification" step actually involves:

Intent Detection: Am I being asked for a fact, a creative story, a technical explanation, or a code snippet?
Safety & Policy Check: Does the request touch on sensitive topics (like the encryption architecture we just discussed) or require specific handling (like avoiding hallucinations)?
Tool Trigger Decision: Do I need to reach out to the outside world?
Is it about Proton? → Trigger proton_info.
Is it about current events or verification? → Trigger web_search.
Is it a static fact or logic puzzle? → Stay internal.
Context Retrieval: Do I need to pull up specific details from our conversation history (like the "three steps" you noticed) to answer coherently?
```

Possible Routed Specialist Agents:
- Fact-Checker (Search & Verification) - optimized for synthesis & citation
- Analyst (Reasoning & Logic) - high-reasoning, chain-of-thought
- Creator (Generative & Creative) - high temperature, creative model
- Archivist (Knowledge Retrieval (RAG)) - fast, low-latency, with access to the RAG tools
- Executor? (Tool Use & Automation) - precise tool integration
- Conversationalist (Chit-Chat & Context) - empathetic