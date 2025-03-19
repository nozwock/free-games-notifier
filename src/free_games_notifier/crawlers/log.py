import logging
import sys


def setup_logging():
    logging.basicConfig(stream=sys.stderr)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
