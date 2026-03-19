from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

from src.internal.ui.theme import BACKGROUND_COLOR, MAIN_COLOR

_theme = Theme(
    {
        # Allows `[text]...[/]` markup if any code opts in.
        "text": MAIN_COLOR,
    }
)

# NOTE: `markup=False` keeps output consistent with `typer.echo` (no Rich markup parsing).
console = Console(
    theme=_theme,
    color_system="truecolor",
    # Set both foreground + background so the terminal is consistent.
    style=f"{MAIN_COLOR} on {BACKGROUND_COLOR}",
    markup=False,
)

console_err = Console(
    theme=_theme,
    color_system="truecolor",
    style=f"{MAIN_COLOR} on {BACKGROUND_COLOR}",
    markup=False,
    stderr=True,
)


def echo(message: object = "", *, err: bool = False) -> None:
    """Rich-backed `echo` compatible with the limited usage in this repo."""
    (console_err if err else console).print(message)
