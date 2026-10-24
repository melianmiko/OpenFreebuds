from PyQt6.QtWidgets import QApplication, QMessageBox

from openfreebuds_backend import is_run_at_boot, set_run_at_boot
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.utils.appimage.integration import install, install_path, is_installed, relaunch
from openfreebuds_qt.utils.qt_utils import exec_msg_box_async


async def appimage_boot(ctx):
    """
    Keep the autostart entry pointing at the installed AppImage,
    and offer installation once when running from another location.
    """
    config = OfbQtConfigParser.get_instance()

    if is_installed():
        if is_run_at_boot():
            await set_run_at_boot(True)
        return

    if config.get("appimage", "install_offered", False):
        return
    config.set("appimage", "install_offered", True)
    config.save()

    box = QMessageBox(QMessageBox.Icon.Question,
                      "OpenFreebuds",
                      QApplication.translate("OfbAppImage",
                                             "Install OpenFreebuds? It will be copied to {} and added to the "
                                             "application menu. You can also do it later from Linux-related "
                                             "settings.").format(install_path().parent),
                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                      ctx.main_window)
    if await exec_msg_box_async(box) != QMessageBox.StandardButton.Yes:
        return

    relaunch(install())
    await ctx.exit()
