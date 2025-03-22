import logging
import sys


def setup_logging(logger: logging.Logger | None = None, loglevel: str | None = None):
    logging.basicConfig(stream=sys.stderr)

    root = logger if logger else logging.getLogger()
    root.setLevel(loglevel if loglevel else logging.INFO)
