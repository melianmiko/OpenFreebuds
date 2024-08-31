import logging
from io import StringIO

log_format = "%(levelname)s:%(name)s:%(threadName)s  %(message)s"

_full_log = StringIO()
handler = logging.StreamHandler(_full_log)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(log_format))


def get_full_log():
    return _full_log.getvalue()


def create_logger(tag: str):
    logger = logging.getLogger(tag)
    logger.addHandler(handler)
    return logger
