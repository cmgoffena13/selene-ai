from rich.console import Console
from rich.theme import Theme

from src.internal.ui.theme import rich_palette


def _make_console(*, stderr: bool) -> Console:
    probe = Console(color_system="auto", stderr=stderr, markup=False)
    palette = rich_palette(getattr(probe, "color_system", None))

    theme = Theme(
        {
            "text": palette["main"],
        }
    )

    return Console(
        theme=theme,
        color_system="auto",
        style=f"{palette['main']} on {palette['background']}",
        markup=False,
        stderr=stderr,
    )


console = _make_console(stderr=False)
console_err = _make_console(stderr=True)


def echo(message: object = "", *, err: bool = False) -> None:
    """Rich-backed `echo` compatible with the limited usage in this repo."""
    (console_err if err else console).print(message)
