.PHONY: format lint test install upgrade docs compile

format: lint
	uv run -- ruff format

lint:
	uv run -- ruff check --fix

test:
	uv run -- pytest -v -n auto

install:
	uv sync --frozen --compile-bytecode --all-extras
	uv run -- prek install -f

upgrade:
	uv sync --upgrade --all-extras

docs:
	PYTHONPATH=. uv run -- typer src.cli.main utils docs --name selene --output docs/cli.md

compile:
	uv run -- nuitka --onefile src/cli/main.py \
		--output-filename=selene \
		--python-flag=no_warnings \
		--include-data-files=pyproject.toml=pyproject.toml \
		--noinclude-data-files=src/tests/* \
		--output-dir=dist/
