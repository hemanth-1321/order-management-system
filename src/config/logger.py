import logging
from enum import StrEnum

LOG_FORMAT_DEBUG = "%(levelname)s | %(asctime)s | %(message)s | %(pathname)s:%(funcName)s:%(lineno)d"

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    debug = "DEBUG"

LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
}
from colorlog import ColoredFormatter

def configure_logging(log_level: str = LogLevels.debug):
    log_level = str(log_level).upper()
    if log_level not in LEVEL_MAP:
        log_level = LogLevels.error.value

    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s | %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )
    logging.basicConfig(level=LEVEL_MAP[log_level], handlers=[handler])
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.info(f"Logging configured at level: {log_level}")
