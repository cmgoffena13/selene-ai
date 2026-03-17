import warnings
from logging.config import dictConfig

import structlog

from src.settings import config


def setup_logging():
    warnings.filterwarnings(
        "ignore",
        message=".*Pydantic serializer warnings.*",
        category=UserWarning,
        module="pydantic.main",
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.render_to_log_kwargs,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handlers = {
        "default": {
            "class": "rich.logging.RichHandler",
            "level": config.LOG_LEVEL,
            "formatter": "console",
            "show_path": False,
        },
    }

    formatters = {
        "console": {
            "class": "logging.Formatter",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
            "format": "%(name)s:%(lineno)d - %(message)s",
        }
    }

    loggers = {
        "src": {
            "level": config.LOG_LEVEL,
            "handlers": list(handlers.keys()),
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
