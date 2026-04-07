# Standards

An evolving document around best practices to achieve reliable results.

## Input Standards
### File Content

```
Filename: [filename]
File contents:
----- BEGIN FILE CONTENTS -----
[actual file content]
----- END FILE CONTENTS -----
```

### SubAgent Results
To be decided upon...

## Prompt Notes

### Context
An agent's context typically includes:
- System instructions — Who the agent is, how it should behave, what rules to follow
- User instructions — The task description and any clarifications
- Conversation history — Previous messages and actions in the current session
- Tool results — Output from searches, file reads, command executions
- Retrieved documents — Information pulled from RAG systems or knowledge bases

### System Prompt Sections
- Who the AI is
- How they speak / interact
- Set the Knowledge Base (ex. Current Date)
- Dos / Donts (Enfore Rules)
- What to do (Task Instruction)

### Prompt Research
- General: https://www.promptingguide.ai
- ChatGPT: https://developers.openai.com/api/docs/guides/prompt-engineering
- Claude: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Gemini: https://cloud.google.com/discover/what-is-prompt-engineering?hl=en
- Llama: https://www.llama.com/docs/how-to-guides/prompting/
- Mistral: https://docs.mistral.ai/capabilities/completion/prompting_capabilities

### Tips & Tricks
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

### Orchestrator Agent
The Orchestrator Agent intakes SubAgent results and synthesizes an appropriate response given the additional information.
- Maintains personality & congruency
- Maintains "general" agent as a fallback

### Planner Agent
Need a planner Agent to best support user experience. This planner agent will:
- Analyze Intent, Complexity, and Required Domain Knowledge.
- Analyze input to determine the agent needed
    - Single Domain? Single-step task?
        - Yes -> route to specialist
        - No -> Give plan of specialists with dependencies
    - Provide agent hints to guide better results

### SubAgents
Possible Routed Specialist Agents:
- Fact-Checker (Search & Verification) - optimized for synthesis & citation
- Analyst (Reasoning & Logic) - high-reasoning, chain-of-thought
- Creator (Generative & Creative) - high temperature, creative model
- Archivist (Knowledge Retrieval (RAG)) - fast, low-latency, with access to the RAG tools
- Executor? (Tool Use & Automation) - precise tool integration
- Conversationalist (Chit-Chat & Context) - empathetic

Specialist Agents return **JSON** strings (validated by Pydantic schemas in each agent’s `schema.py`).

### RAG
LLM APIs do not have a `context` role, so providing information to the orchestrator needs to happen in the `user` or `system` message. Pivoting to try the `user` message approach. This requires:
- An injection into the user prompt
- A system prompt for the orchestrator to NOT mention the injected data to the user
- A function to trim out the injected data in the UI