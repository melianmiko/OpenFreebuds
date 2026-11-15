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


def _make_file_handler():
    """把完整日志同时写一份文件，方便排查 GUI 里「点了没反应」这类问题。"""
    try:
        from openfreebuds.constants import STORAGE_PATH
        log_dir = STORAGE_PATH / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "openfreebuds.log", encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(log_format_with_time))
        return handler
    except Exception:
        return None


def setup_logging(screen_verbose: bool = False):
    screen_handler.setLevel(logging.DEBUG if screen_verbose else logging.WARN)
    handlers = [memory_handler, screen_handler]
    file_handler = _make_file_handler()
    if file_handler is not None:
        handlers.append(file_handler)
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)


def get_full_log():
    return _full_log.getvalue()


def create_logger(tag: str):
    return logging.getLogger(tag)
