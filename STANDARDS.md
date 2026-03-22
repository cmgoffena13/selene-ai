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

Research:
- https://developers.openai.com/api/docs/guides/prompt-engineering
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- https://cloud.google.com/discover/what-is-prompt-engineering?hl=en