import logging
import sys


def setup_logging(loglevel: str | None = None):
    logging.basicConfig(stream=sys.stderr)

    root = logging.getLogger()
    root.setLevel(loglevel if loglevel else logging.INFO)
