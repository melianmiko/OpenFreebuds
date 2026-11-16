"""Qt exit must stop the manager even in client mode."""
import asyncio
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import importlib

main_module = importlib.import_module("openfreebuds_qt.main")
from openfreebuds_qt.main import OfbQtApplication


@pytest.mark.asyncio
async def test_exit_destroys_manager_in_client_mode():
    calls = []

    class _Ofb:
        role = "client"

        async def destroy(self):
            calls.append("destroy")

    class _Tray:
        async def close(self):
            calls.append("tray")

    fake = SimpleNamespace(
        tray=_Tray(),
        main_window=SimpleNamespace(hide=lambda: calls.append("hide")),
        ofb=_Ofb(),
        _exit=lambda code: calls.append(("exit", code)),
    )

    await OfbQtApplication.exit(fake, 0)

    assert calls == ["tray", "hide", "destroy", ("exit", 0)]


@pytest.mark.asyncio
async def test_exit_still_quits_when_destroy_connection_drops():
    calls = []

    class _Ofb:
        role = "client"

        async def destroy(self):
            raise ConnectionResetError("RPC server stopped")

    class _Tray:
        async def close(self):
            pass

    fake = SimpleNamespace(
        tray=_Tray(),
        main_window=SimpleNamespace(hide=lambda: None),
        ofb=_Ofb(),
        _exit=lambda code: calls.append(code),
    )

    await OfbQtApplication.exit(fake, 0)

    assert calls == [0]


@pytest.mark.asyncio
async def test_exit_returns_when_manager_stop_hangs(monkeypatch):
    monkeypatch.setattr(main_module, "EXIT_SHUTDOWN_TIMEOUT", 0.1)
    calls = []

    class _Ofb:
        role = "standalone"

        async def destroy(self):
            await asyncio.sleep(10)

    class _Tray:
        async def close(self):
            pass

    fake = SimpleNamespace(
        tray=_Tray(),
        main_window=SimpleNamespace(hide=lambda: None),
        ofb=_Ofb(),
        _exit=lambda code: calls.append(code),
    )

    await asyncio.wait_for(OfbQtApplication.exit(fake, 0), timeout=1)

    assert calls == [0]
