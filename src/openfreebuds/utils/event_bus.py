from uuid import uuid4


class Subscription:
    def __init__(self):
        self._callbacks = {}        # type: dict[str, tuple[list[str] | None, callable]]

    async def message(self, kind: str, *args, **kwargs):
        for kind_filters, callback in self._callbacks.values():
            if kind_filters is not None and kind not in kind_filters:
                continue
            callback(kind, *args, **kwargs)

    def subscriber(
            self,
            kind_filters: list[str] | None = None,
            callback_id: str = None
    ):
        def _wrapper(func):
            self.subscribe(func, kind_filters, callback_id)
            return func

        return _wrapper

    def subscribe(
            self,
            callback,
            kind_filters: list[str] | None = None,
            callback_id: str = None
    ):
        if callback_id is None:
            callback_id = uuid4()

        self._callbacks[callback_id] = (kind_filters, callback)

    def unsubscribe(self, callback_id: str):
        del self._callbacks[callback_id]
