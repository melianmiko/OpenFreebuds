from collections.abc import Iterable, Sequence

from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QLayout, QSizePolicy, QVBoxLayout, QWidget


def clear_layout(layout: QLayout, keep_widgets: Iterable[QWidget] | None = None):
    keep = set(keep_widgets or [])
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        widget = item.widget()

        if child_layout is not None:
            clear_layout(child_layout, keep)
            continue

        if widget is None:
            continue

        if widget not in keep:
            widget.hide()
            widget.setParent(None)


def populate_rows(layout: QLayout, rows: Sequence[QWidget], column_span: int = 1):
    if isinstance(layout, QGridLayout):
        for row_index, row in enumerate(rows):
            layout.addWidget(row, row_index, 0, 1, column_span)
        return

    for row in rows:
        layout.addWidget(row)


def make_settings_row(parent: QWidget,
                      title: str,
                      description: str = "",
                      controls: Sequence[QWidget] | None = None) -> QWidget:
    row = QWidget(parent)
    row.setProperty("settingsRow", True)
    row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    root_layout = QHBoxLayout(row)
    root_layout.setContentsMargins(18, 16, 18, 16)
    root_layout.setSpacing(18)

    text_root = QWidget(row)
    text_root.setProperty("settingsTextBlock", True)
    text_layout = QVBoxLayout(text_root)
    text_layout.setContentsMargins(0, 0, 0, 0)
    text_layout.setSpacing(4)

    title_label = QLabel(title, text_root)
    title_label.setProperty("settingsRowTitle", True)
    title_label.setWordWrap(True)
    text_layout.addWidget(title_label)

    if description:
        description_label = QLabel(description, text_root)
        description_label.setProperty("settingsRowDescription", True)
        description_label.setWordWrap(True)
        text_layout.addWidget(description_label)

    root_layout.addWidget(text_root, 1)

    if controls:
        controls_root = QWidget(row)
        controls_root.setProperty("settingsControls", True)
        controls_layout = QHBoxLayout(controls_root)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        for control in controls:
            controls_layout.addWidget(control)
        root_layout.addWidget(controls_root, 0)

    return row