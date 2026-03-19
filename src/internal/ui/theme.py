from typing import Any

MAIN_COLOR = "#0E76D3"  # Main color, used for text (branding)
BACKGROUND_COLOR = "#020303"  # Background Color, black

# Grayer color, color of text boxes / widget surfaces
SURFACE_COLOR = "#1B2126"

# Mellow blue. Use for borders / accents
BORDER_COLOR = "#295A86"

# Use wherever to even out (panels / secondary surfaces)
PANEL_COLOR = "#2C4053"


RICH_ANSI = {
    "main": "white",
    "background": "black",
    "surface": "bright_black",
    "border": "white",
    "panel": "bright_black",
}

TEXTUAL_ANSI = {
    "main": "ansi_white",
    "background": "ansi_black",
    "surface": "ansi_bright_black",
    "border": "ansi_white",
    "panel": "ansi_bright_black",
}


def _is_truecolor(color_system: Any) -> bool:
    """
    Best-effort detection of truecolor support.

    `color_system` may be a string ("truecolor") or an enum-like object from Rich.
    """
    normalized = getattr(color_system, "value", None) or str(color_system or "")
    return "truecolor" in str(normalized).lower()


def rich_palette(color_system: Any) -> dict[str, str]:
    return (
        {
            "main": MAIN_COLOR,
            "background": BACKGROUND_COLOR,
            "surface": SURFACE_COLOR,
            "border": BORDER_COLOR,
            "panel": PANEL_COLOR,
        }
        if _is_truecolor(color_system)
        else RICH_ANSI
    )


def textual_palette(color_system: Any) -> dict[str, str]:
    return (
        {
            "main": MAIN_COLOR,
            "background": BACKGROUND_COLOR,
            "surface": SURFACE_COLOR,
            "border": BORDER_COLOR,
            "panel": PANEL_COLOR,
        }
        if _is_truecolor(color_system)
        else TEXTUAL_ANSI
    )
