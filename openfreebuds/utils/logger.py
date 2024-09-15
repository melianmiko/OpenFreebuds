import logging
import sys
from io import StringIO

log_format = "%(levelno)s:%(name)s  %(message)s"
log_format_with_time = f"%(relativeCreated)d:{log_format}"

_full_log = StringIO()

memory_handler = logging.StreamHandler(_full_log)
memory_handler.setLevel(logging.DEBUG)
memory_handler.setFormatter(logging.Formatter(log_format_with_time))

screen_handler = logging.StreamHandler(sys.stdout)
screen_handler.setFormatter(logging.Formatter(log_format))


def setup_logging(screen_verbose: bool = False):
    screen_handler.setLevel(logging.DEBUG if screen_verbose else logging.WARN)
    logging.basicConfig(level=logging.DEBUG, handlers=[memory_handler, screen_handler])


def get_full_log():
    return _full_log.getvalue()


def create_logger(tag: str):
    return logging.getLogger(tag)
