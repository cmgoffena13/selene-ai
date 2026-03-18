# `selene`

Selene AI - Local Death Dealer Assistant

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
* `model`: Manage Ollama models (pull, list).
* `chat`: Open an interactive chat with Selene.

## `selene ask`

Ask Selene a question

**Usage**:

```console
$ selene ask [OPTIONS] PROMPT
```

**Arguments**:

* `PROMPT`: What to ask the model  [required]

**Options**:

* `--help`: Show this message and exit.

## `selene model`

Manage Ollama models (pull, list).

**Usage**:

```console
$ selene model [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `list`: List Ollama models available locally.
* `pull`: Pull an Ollama model so you can use it...

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

## `selene chat`

Open an interactive chat with Selene.

**Usage**:

```console
$ selene chat [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.
