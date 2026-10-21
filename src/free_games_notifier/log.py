"""
Reference:
https://github.com/Open-Wine-Components/umu-launcher/blob/e2b203a1fdd2af9f35166f5713cb3f85d72587e2/umu/umu_log.py
"""

import copy
import logging
import os
import sys
from pathlib import Path
from typing import TextIO

from free_games_notifier.config import DIST_NAME


class Color:
    ERROR = "\033[31m"  # Red
    DEBUG = "\u001b[35m"  # Purple
    INFO = "\u001b[34m"  # Blue
    WARNING = "\033[33m"  # Yellow
    CRITICAL = "\033[33m"  # Yellow
    BOLD = "\033[1m"
    GREY = "\033[90m"
    RESET = "\u001b[0m"


SIMPLE_FORMAT = "%(levelname)s: %(message)s"
DEBUG_FORMAT = "%(levelname)-8s [%(pathname)s:%(lineno)d]: %(message)s"


class CustomFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        stream: TextIO | None = None,
        is_debug: bool = False,
    ) -> None:
        super().__init__(fmt)
        self.stream: TextIO = stream if stream is not None else sys.stderr
        self.is_debug = is_debug

    def format(self, record: logging.LogRecord) -> str:
        record = copy.copy(record)
        if self.is_debug:
            try:
                record.pathname = os.path.relpath(record.pathname, Path.cwd())
            except (ValueError, OSError):
                ...

        if not self._should_colorize():
            return super().format(record)

        color: str
        match record.levelname:
            case "INFO":
                color = Color.INFO
            case "DEBUG":
                color = Color.DEBUG
            case "CRITICAL":
                color = Color.CRITICAL
            case "ERROR":
                color = Color.ERROR
            case "WARNING" | "WARN":
                color = Color.WARNING
            case "FATAL":
                color = Color.WARNING
            case _:
                color = Color.BOLD

        levelname = record.levelname
        if self.is_debug:
            levelname = f"{levelname:<8}"
        record.levelname = f"{color}{Color.BOLD}{levelname}{Color.RESET}"

        return super().format(record)

    def _should_colorize(self) -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        try:
            return bool(hasattr(self.stream, "isatty") and self.stream.isatty())
        except (ValueError, OSError):
            return False


def setup_logging(level: str | int = 0) -> None:
    is_debug = level in {logging.DEBUG, "DEBUG"}
    fmt = DEBUG_FORMAT if is_debug else SIMPLE_FORMAT

    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setFormatter(
        CustomFormatter(fmt, stream=sys.stderr, is_debug=is_debug)
    )

    logging.basicConfig(handlers=[console_handler], level=level, force=True)

    target_logger = logging.getLogger()
    target_logger.setLevel(level)
