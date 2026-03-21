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

## Notes
An agent's context typically includes:
- System instructions — Who the agent is, how it should behave, what rules to follow
- User instructions — The task description and any clarifications
- Conversation history — Previous messages and actions in the current session
- Tool results — Output from searches, file reads, command executions
- Retrieved documents — Information pulled from RAG systems or knowledge bases