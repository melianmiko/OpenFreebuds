from PyQt6.QtWidgets import QWidget, QLabel

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.generic import IOfbQtApplication

log = create_logger("OfbQtUpdateWidgetHelper")


class OfbQtUpdateWidgetHelper:
    def __init__(self, root_widget: QWidget, label_widget: QLabel, ctx: IOfbQtApplication):
        self.config = OfbQtConfigParser.get_instance()
        self.root_widget = root_widget
        self.label_widget = label_widget
        self.ctx = ctx

    def update_widget(self):
        updater = self.ctx.updater_service.updater
        if updater is None:
            self.root_widget.setVisible(False)
            return

        log.info(f"{updater.has_update} {updater.release_info}")
        if updater.has_update:
            if updater.release_info.version == self.config.get("updater", "ignored_version", ""):
                self.root_widget.setVisible(False)
                return
            self.label_widget.setText(f"{updater.config.app_display_name} {updater.release_info.version}")
        self.root_widget.setVisible(updater.has_update)

    def user_hide(self):
        updater = self.ctx.updater_service.updater
        if updater is None:
            self.root_widget.setVisible(False)
            return

        self.config.set("updater", "ignored_version", updater.release_info.version)
        self.config.save()

        self.root_widget.setVisible(False)
