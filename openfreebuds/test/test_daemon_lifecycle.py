"""Daemon lifetime: the process must end when its RPC server task ends."""
import asyncio

import pytest

from openfreebuds import main as daemon_main


@pytest.mark.asyncio
async def test_main_returns_when_server_task_finishes(monkeypatch):
    class _FakeManager:
        role = "standalone"

        def __init__(self):
            self.server_task = asyncio.create_task(asyncio.sleep(0))

        async def destroy(self):
            pass

    async def _fake_create(*_args, **_kwargs):
        return _FakeManager()

    monkeypatch.setattr(daemon_main, "create", _fake_create)

    await asyncio.wait_for(daemon_main.main(), timeout=1)
