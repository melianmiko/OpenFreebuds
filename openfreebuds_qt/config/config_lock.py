import os
import sys
from pathlib import Path

from psutil import Process, AccessDenied, NoSuchProcess

from openfreebuds.constants import STORAGE_PATH
from openfreebuds.utils.logger import create_logger

log = create_logger("ConfigLock")


class ConfigLock:
    _path: Path = STORAGE_PATH / "openfreebuds_qt.pid"
    owned: bool = False

    @staticmethod
    def acquire():
        if ConfigLock._path.is_file():
            try:
                with open(ConfigLock._path, "r") as f:
                    process = Process(int(f.read()))
                    log.info(f"{Path(process.exe())}, {Path(sys.executable).resolve()}")
                    if os.getpid() != process.pid and Path(process.exe()) == Path(sys.executable).resolve():
                        # Found already running instance, non-exclusive lock
                        ConfigLock.owned = False
                        return
            except (AccessDenied, NoSuchProcess) as e:
                log.info(e)

        with open(ConfigLock._path, "w") as f:
            f.write(str(os.getpid()))

        log.info(f"Lock acquired, path={ConfigLock._path}")
        ConfigLock.owned = True

    @staticmethod
    def release():
        if ConfigLock.owned and ConfigLock._path.is_file():
            os.remove(ConfigLock._path)
            log.info("Lock released")
