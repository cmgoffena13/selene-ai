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

## Tool Output

```
Tool: [tool name]
Tool Query: [query]
Tool Result:
----- BEGIN TOOL RESULT -----
[tool result content]
----- END TOOL RESULT -----
```

## System Prompt Sections
- Identity & Personality
    - Critical Thinking & Engagement Principles
- Tool Usage
- File Handling

hmmmm, so maybe this standard (so far):
- identity.md (only need one of these)
- tools.md
- files.md

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