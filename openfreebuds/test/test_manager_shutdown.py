"""Manager shutdown must not hang on a driver that ignores cancellation."""
import asyncio

import pytest

import openfreebuds.manager.main as manager_main


@pytest.mark.asyncio
async def test_stop_returns_when_mainloop_ignores_cancellation(monkeypatch):
    monkeypatch.setattr(manager_main, "SHUTDOWN_TIMEOUT", 0.2)
    manager = manager_main.OfbManager()
    started = asyncio.Event()

    async def _stuck():
        started.set()
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            # Simulate a driver call that does not finish when cancelled.
            await asyncio.sleep(0.35)

    manager._task = asyncio.create_task(_stuck())
    await started.wait()

    class _Driver:
        async def stop(self):
            pass

    manager._driver = _Driver()

    await asyncio.wait_for(manager.stop(), timeout=1)

    assert manager._task is None
    assert manager._driver is None
