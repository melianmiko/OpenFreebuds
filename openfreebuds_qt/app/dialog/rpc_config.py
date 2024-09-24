import sys
import json
from contextlib import suppress

from PyQt6.QtWidgets import QWidget

from openfreebuds import STORAGE_PATH
from openfreebuds_qt.constants import WIN32_BODY_STYLE
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.designer.stupid_rpc_setup import Ui_Dialog
from openfreebuds_qt.utils import OfbQtAsyncDialog

log = create_logger("OfbQtRpcConfig")


class OfbQtRpcConfig(Ui_Dialog, OfbQtAsyncDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)
        if sys.platform == "win32":
            self.setStyleSheet(WIN32_BODY_STYLE)

        self.current_config = {}
        with suppress(Exception):
            with open(STORAGE_PATH / "openfreebuds_rpc.json", "r") as f:
                self.current_config = json.load(f)

        self.cb_remote_access.setChecked(self.current_config.get("allow_remote", False))
        self.cb_secret_key.setChecked(self.current_config.get("require_authorization", False))
        self.field_secret.setText(self.current_config.get("secret_key", ""))

    async def get_user_response(self):
        res = await super().get_user_response()
        if not res:
            return

        # Save settings
        with open(STORAGE_PATH / "openfreebuds_rpc.json", "w") as f:
            json.dump({
                "allow_remote": self.cb_remote_access.isChecked(),
                "require_authorization": self.cb_secret_key.isChecked(),
                "secret_key": self.field_secret.text(),
            }, f)
