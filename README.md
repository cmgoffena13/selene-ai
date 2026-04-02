# Selene

```text
 ____       _                 
/ ___|  ___| | ___ _ __   ___ 
\___ \ / _ \ |/ _ \ '_ \ / _ \
 ___) |  __/ |  __/ | | |  __/
|____/ \___|_|\___|_| |_|\___|
```

![Lines of Code](https://aschey.tech/tokei/github/cmgoffena13/selene-ai?category=code)
[![Build Status](https://github.com/cmgoffena13/selene-ai/actions/workflows/build-release.yml/badge.svg)](https://github.com/cmgoffena13/selene-ai/actions)
![License](https://img.shields.io/badge/license-MIT-informational?style=flat)

> *"Like the weapons of the previous century, we too would become obsolete. Pity, because I lived for it"*

Selene is a local command-line AI powered by [Ollama](https://ollama.com) & [Thoughtflow](https://github.com/jrolf/thoughtflow/tree/main)

---

## Setup
- Download the latest zip in releases
  - Extract the zip
  - Add the `selene` binary in the folder to your PATH
- Have [Ollama](https://ollama.ai) installed and running
- Place a `.env` file in the config directory (Utilize `selene --info` to locate)
  - `SELENE_OLLAMA_MODEL` (Required) Recommended: `llama3-groq-tool-use:8b`
  - `SELENE_OLLAMA_EMBEDDING_MODEL` (Optional) Default: `nomic-embed-text`
  - `SELENE_TAVILY_API_KEY` (Optional)

## Capabilities
 - **Intelligence on Demand**: Ask questions, Analyze files, etc. via [Typer](https://github.com/fastapi/typer) CLI
 - **Interactive Chat**: Conversation mode with persistent memory via [Textual](https://github.com/Textualize/textual) GUI
 - **Local Search**: Index your local files via [LEANN](https://github.com/yichuan-w/LEANN) vector indexes
 - **Web Search**: Real-time web search via [Tavily](https://www.tavily.com)

## Usage Examples

```bash
# Ask a simple question
selene ask "Why did Kraven fail?"

# Search the archives
selene ask "What does it say about hybrids?" --file ancient.txt

# Consult Selene's wisdom
selene chat

# Share persistent resources with Selene
selene rag index my-documents --dir C:/directory/path/

# Real-time observation (Tavily API Key Required)
selene ask "What is the status on the development of Silver Nitrate?"
```

## Interactive Chat

Interact with Selene in a remembered conversation. 

`selene chat --web`  

![Chat Window](static/textualize.png)