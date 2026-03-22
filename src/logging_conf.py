from logging.config import dictConfig
from typing import Any

from src.settings import config


def setup_logging():
    handlers: dict[str, Any] = {
        "default": {
            "class": "logging.StreamHandler",
            "level": str(config.SELENE_LOG_LEVEL),
            "formatter": "console",
        },
    }

    formatters: dict[str, Any] = {
        "console": {
            "class": "logging.Formatter",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
            "format": "%(name)s:%(lineno)d - %(message)s",
        }
    }

    loggers: dict[str, Any] = {
        "src": {
            "level": str(config.SELENE_LOG_LEVEL),
            "handlers": ["default"],
            "propagate": False,
        }
    }

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": loggers,
        }
    )
