# `selene`

Selene AI - Death Dealer, Elder Slayer, Silent Watcher

**Usage**:

```console
$ selene [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--version`: Show CLI version and exit
* `--info`: Show general CLI info and exit
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `ask`: Ask Selene a question
* `model`: Manage Ollama models (pull, list, remove).
* `chat`: Open an interactive chat with Selene.
* `rag`: Build and manage RAG indexes (stored in...

## `selene ask`

Ask Selene a question

**Usage**:

```console
$ selene ask [OPTIONS] PROMPT
```

**Arguments**:

* `PROMPT`: What to ask the model  [required]

**Options**:

* `-f, --file TEXT`: Attach a file to analyze.
* `-v, --verbose`: Show verbose output.
* `--help`: Show this message and exit.

## `selene model`

Manage Ollama models (pull, list, remove).

**Usage**:

```console
$ selene model [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `list`: List Ollama models available locally.
* `pull`: Pull an Ollama model so you can use it...
* `delete`

### `selene model list`

List Ollama models available locally.

**Usage**:

```console
$ selene model list [OPTIONS]
```

**Options**:

* `-H, --host TEXT`: Ollama host  [default: http://localhost:11434]
* `--help`: Show this message and exit.

### `selene model pull`

Pull an Ollama model so you can use it with Selene.

**Usage**:

```console
$ selene model pull [OPTIONS] NAME
```

**Arguments**:

* `NAME`: Model name (e.g. llama3.2, mistral)  [required]

**Options**:

* `-H, --host TEXT`: Ollama host  [default: http://localhost:11434]
* `--help`: Show this message and exit.

### `selene model delete`

**Usage**:

```console
$ selene model delete [OPTIONS] NAME
```

**Arguments**:

* `NAME`: Model name to remove (e.g. llama3.2)  [required]

**Options**:

* `-H, --host TEXT`: Ollama host  [default: http://localhost:11434]
* `--help`: Show this message and exit.

## `selene chat`

Open an interactive chat with Selene.

**Usage**:

```console
$ selene chat [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-w, --web`: Serve chat UI in a web browser.
* `-c, --classic`: Use the classic Thoughtflow chat.
* `-v, --verbose`: Show full ThoughtFlow memory in the transcript (all roles, logs, refs, vars).
* `--help`: Show this message and exit.

## `selene rag`

Build and manage RAG indexes (stored in ~/.config/selene_ai).

**Usage**:

```console
$ selene rag [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `index`: Create a RAG index from a directory.
* `update`: Update an existing RAG index with new...
* `list`: List RAG indexes with size (GB) and docs...
* `delete`: Delete a stored RAG index by name.

### `selene rag index`

Create a RAG index from a directory. Supported: .pdf, .docx, .pptx, .csv, .epub, .mbox, .ipynb, .xls, .xlsx, images (.gif, .jpg, .png, .jpeg, .webp), audio/video (.mp3, .mp4), .hwp. Other files (e.g. .py, .md, .txt) are read as plain text.

**Usage**:

```console
$ selene rag index [OPTIONS] NAME
```

**Arguments**:

* `NAME`: Index name (e.g. my-docs). Used to look up the index later.  [required]

**Options**:

* `-d, --dir TEXT`: Directory path of files to index (recursive). Supported: .pdf, .docx, .pptx, .csv, .epub, .mbox, .ipynb, .xls, .xlsx, images (.gif, .jpg, .png, .jpeg, .webp), audio/video (.mp3, .mp4), .hwp. Other files (e.g. .py, .md, .txt) are read as plain text.  [required]
* `--help`: Show this message and exit.

### `selene rag update`

Update an existing RAG index with new files from its stored docs directory (add-only for HNSW).

**Usage**:

```console
$ selene rag update [OPTIONS] NAME
```

**Arguments**:

* `NAME`: Index name to update.  [required]

**Options**:

* `--help`: Show this message and exit.

### `selene rag list`

List RAG indexes with size (GB) and docs directory.

**Usage**:

```console
$ selene rag list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `selene rag delete`

Delete a stored RAG index by name.

**Usage**:

```console
$ selene rag delete [OPTIONS] NAME
```

**Arguments**:

* `NAME`: Index name to delete (e.g. my-docs).  [required]

**Options**:

* `--help`: Show this message and exit.
