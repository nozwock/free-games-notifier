import logging
import sys


def setup_logging():
    logging.basicConfig(stream=sys.stderr)

    root = logging.getLogger()
    # todo: get log level from env
    root.setLevel(logging.DEBUG)
