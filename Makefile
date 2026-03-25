.PHONY: format lint test install upgrade docs compile compile-zip

format: lint
	uv run -- ruff format

lint:
	uv run -- ruff check --fix
	uv run -- ty check

test:
	uv run -- pytest -v -n auto

install:
	uv sync --frozen --compile-bytecode --all-extras
	uv run -- prek install -f

upgrade:
	uv sync --upgrade --all-extras

docs:
	PYTHONPATH=. uv run -- typer src.cli.selene utils docs --name selene --output docs/cli.md

compile:
	uv run -- nuitka src/cli/selene.py \
		--lto=yes \
		--output-filename=selene \
		--python-flag=no_warnings \
		--include-data-files=pyproject.toml=pyproject.toml \
		--noinclude-data-files=src/tests/* \
		--output-dir=dist/

compile-zip: compile
	cd dist && rm -f selene-dist.zip && zip -r selene-dist.zip selene.dist
