import uuid
import logging.config

from contextvars import ContextVar, Token


_tracing_context: ContextVar[uuid.uuid4] = ContextVar("_tracing_context", default=uuid.uuid4())


class CustomLoggingFormatter(logging.Formatter):
    """
    Logging with ANSI color codes
    """

    format_header = "%(asctime)s - %(name)s - "
    format_content = "%(message)s (%(filename)s:%(lineno)d) "
    format_tracing = "[%(tracing_value)s]"

    c_fg_black = "\x1b[30m"
    c_fg_red = "\x1b[31m"
    c_fg_green = "\x1b[32m"
    c_fg_yellow = "\x1b[33m"
    c_fg_blue = "\x1b[34m"
    c_fg_magenta = "\x1b[35m"
    c_fg_cyan = "\x1b[36m"
    c_fg_white = "\x1b[37m"
    c_fg_crimson = "\x1b[38m"
    c_reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: c_fg_magenta + format_header + c_fg_white + format_content + c_fg_cyan + format_tracing + c_reset,
        logging.INFO: c_fg_magenta + format_header + c_reset + format_content + c_fg_cyan + format_tracing + c_reset,
        logging.WARNING: c_fg_magenta + format_header + c_fg_yellow + format_content + c_fg_cyan + format_tracing + c_reset,
        logging.ERROR: c_fg_magenta + format_header + c_fg_red + format_content + c_fg_cyan + format_tracing + c_reset,
        logging.CRITICAL: c_fg_magenta + format_header + c_fg_red + format_content + c_fg_cyan + format_tracing + c_reset
    }

    def format(self, record):
        record.tracing_value = _tracing_context.get()
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {
            '()': "core.logging.CustomLoggingFormatter",
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "base"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.error": {
            "disabled": True
        },
        "uvicorn.access": {
            "disabled": True
        },
        "httpx": {
            "level": "CRITICAL",
            "handlers": [],
            "propagate": True,
            "disabled": True
        },
        "httpcore": {
            "level": "CRITICAL",
            "handlers": [],
            "propagate": True,
            "disabled": True
        }
    }
}


def setup_logger():
    logging.config.dictConfig(config=LOGGING_CONFIG)


def set_tracing_context(tracing_value: uuid.uuid4) -> Token:
    return _tracing_context.set(tracing_value)


def get_tracing_context() -> uuid.uuid4:
    return _tracing_context.get()


def reset_session_context(context: Token) -> None:
    _tracing_context.reset(context)
