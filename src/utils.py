import sys
import time
import tomllib
from functools import wraps
from pathlib import Path

import structlog

logger = structlog.getLogger(__name__)


def retry(attempts: int = 3, delay: float = 0.25, backoff: float = 2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for index in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if index == attempts - 1:
                        raise e
                    logger.warning(
                        f"Retrying {func.__name__} (attempt {index + 2}/{attempts}) after {type(e).__name__}: {e}"
                    )
                    time.sleep(wait)
                    wait *= backoff

        return wrapper

    return decorator


def get_version() -> str:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if not isinstance(meipass, str):
            raise RuntimeError("frozen build missing sys._MEIPASS")
        base_path = Path(meipass)
        pyproject_path = base_path / "pyproject.toml"
        if not pyproject_path.exists():
            exe_path = Path(
                sys.executable if hasattr(sys, "executable") else sys.argv[0]
            )
            pyproject_path = exe_path.parent / "pyproject.toml"
    else:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"Could not find pyproject.toml at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if missing; return the same path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_selene_ai_config_dir(*parts: str) -> Path:
    """
    Base directory for Selene local config/data: ~/.config/selene_ai

    If `parts` are provided, returns ~/.config/selene_ai/<parts...> and creates it.
    """
    base = Path.home() / ".config" / "selene_ai"
    return ensure_dir(base.joinpath(*parts))
