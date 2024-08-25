from PyQt6.QtWidgets import QComboBox


def fill_combo_box(box: QComboBox, options: list[str], name_map: dict[str, str], current: str):
    box.blockSignals(True)
    box.clear()
    box.addItems([box.tr(name_map.get(i, i)) for i in options])
    for index, value in enumerate(options):
        box.setItemData(index, value)

    if current in options:
        box.setCurrentIndex(options.index(current))
    else:
        box.setCurrentIndex(-1)

    box.blockSignals(False)
