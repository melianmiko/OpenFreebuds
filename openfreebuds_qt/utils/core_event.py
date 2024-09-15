from typing import Optional

from openfreebuds import OfbEventKind


class OfbCoreEvent:
    def __init__(self, kind: Optional[str], *args):
        self._kind = kind
        self.args = args

    def __str__(self):
        return f"<OfbCoreEvent kind={self._kind}, args={self.args}>"

    def kind_match(self, kind: str):
        return self._kind is None or self._kind == kind

    def kind_in(self, kinds: list[str]):
        return self._kind is None or self._kind in kinds

    def is_prop_group_in(self, groups: list[str]):
        if self._kind is None:
            return True
        if self._kind != OfbEventKind.PROPERTY_CHANGED:
            return False
        ch_group, *_ = (*self.args, "", "")
        return ch_group in groups

    def is_changed(self, group: str, prop: str = None):
        if self._kind is None:
            return True
        if self._kind != OfbEventKind.PROPERTY_CHANGED:
            return False
        ch_group, ch_prop, *_ = (*self.args, "", "")
        if ch_group == "":
            return True
        if ch_group == group and (prop is None or ch_prop is None or ch_prop == prop):
            return True
        return False
