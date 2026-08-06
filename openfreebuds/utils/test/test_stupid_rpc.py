"""Tests for StupidRPC server hardening"""

import asyncio
import json

import aiohttp
import pytest

from openfreebuds.utils import stupid_rpc


class FakeInstance:
    async def ping_value(self):
        return "pong"


async def _serve(**kwargs):
    """Start the RPC server in the background, return its task."""
    task = asyncio.create_task(stupid_rpc.run_rpc_server(FakeInstance(), **kwargs))
    await asyncio.sleep(0.3)
    return task


async def _stop(task):
    task.cancel()
    with_suppress = (asyncio.CancelledError,)
    try:
        await task
    except with_suppress:
        pass
    await asyncio.sleep(0.1)


async def _post(path, secret=None):
    headers = {"Content-Type": "application/json"}
    if secret is not None:
        headers["X-Secret"] = secret
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://127.0.0.1:{stupid_rpc._PORT}/__rpc__/{path}",
            data=json.dumps({"args": [], "kwargs": {}}),
            headers=headers,
        ) as resp:
            return resp.status, await resp.text()


@pytest.mark.asyncio
async def test_remote_without_key_falls_back_to_local():
    """Binding on 0.0.0.0 must be refused when no secret key is configured"""
    task = await _serve(allow_remote=True, require_authorization=False)
    try:
        # Server must still answer on loopback ...
        status, _ = await _post("ping_value")
        assert status == 200

        # ... but must not be reachable from a non-loopback address
        with pytest.raises(OSError):
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.2", stupid_rpc._PORT), timeout=1
            )
            writer.close()
    finally:
        await _stop(task)


@pytest.mark.asyncio
async def test_empty_secret_key_is_not_an_authorization():
    """require_authorization with an empty key used to accept any request"""
    task = await _serve(allow_remote=True, require_authorization=True, secret_key="")
    try:
        # Empty key means "not configured", so remote access is refused
        with pytest.raises(OSError):
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.2", stupid_rpc._PORT), timeout=1
            )
            writer.close()
    finally:
        await _stop(task)


@pytest.mark.asyncio
async def test_wrong_key_rejected():
    """A configured key must actually be enforced"""
    task = await _serve(require_authorization=True, secret_key="s3cret")
    try:
        assert (await _post("ping_value", secret="wrong"))[0] == 401
        assert (await _post("ping_value"))[0] == 401
        assert (await _post("ping_value", secret="s3cret"))[0] == 200
    finally:
        await _stop(task)


@pytest.mark.asyncio
async def test_local_only_by_default():
    """Default configuration must stay bound to loopback"""
    task = await _serve()
    try:
        assert (await _post("ping_value"))[0] == 200
        with pytest.raises(OSError):
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.2", stupid_rpc._PORT), timeout=1
            )
            writer.close()
    finally:
        await _stop(task)
