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

create-base-db:
	uv run -- python -m src.database.db create_base_db