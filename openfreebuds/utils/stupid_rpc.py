import asyncio
import json
import logging
import traceback

import aiohttp
from aiohttp import web
from aiohttp.web_response import json_response

from openfreebuds.exceptions import OfbServerDeadError
from openfreebuds.utils.logger import create_logger

_PORT = 19823
log = create_logger("StupidRPC")


class RemoteError(Exception):
    def __init__(self, data):
        super().__init__(data)
        self.rpc_trace = data["trace"]
        self.args = data["args"]

    def __str__(self):
        return f"Got server-side error:\n\n{self.rpc_trace}"


def rpc(func):
    async def _inner(self, *args, **kwargs):
        if self.role == "client":
            while True:
                try:
                    return await do_rpc_request(func.__name__, self.rpc_config, *args, **kwargs)
                except aiohttp.ClientConnectionError:
                    raise OfbServerDeadError("Server is down, please restart application")
        return await func(self, *args, **kwargs)

    return _inner


async def do_rpc_request(func, config, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://127.0.0.1:{_PORT}/__rpc__/{func}",
                data=json.dumps({
                    "args": args,
                    "kwargs": kwargs,
                }),
                headers={
                    "Content-Type": "application/json",
                    "X-Secret": config.get("secret_key", "")
                }
        ) as resp:
            data = json.loads(await resp.text())
            if resp.status == 500:
                raise RemoteError(data)
            return data


async def test_online():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://127.0.0.1:{_PORT}/__rpc__/ping") as resp:
            assert resp.status == 200


# noinspection PyBroadException
async def _handle_rpc_call(instance, request: web.Request, data=None):
    target = '' if 'path' not in request.match_info else request.match_info['path']

    if data is None:
        data = {"args": [], "kwargs": {}}

    if getattr(instance, target, None) is not None:
        # Call remote process and return result
        try:
            result = await getattr(instance, target)(*data['args'], **data['kwargs'])
            return web.Response(status=200,
                                text=json.dumps(result),
                                content_type="application/json")
        except Exception as e:
            # log.exception(e)
            return web.Response(status=500,
                                text=json.dumps({
                                    "class": e.__class__.__name__,
                                    "trace": traceback.format_exc(),
                                    "args": e.args
                                }))
    else:
        return web.Response(status=200, text="ok")


async def run_rpc_server(
        instance,
        allow_remote: bool = False,
        require_authorization: bool = False,
        secret_key: str = "",
):
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

    host = "127.0.0.1" if not allow_remote else "0.0.0.0"
    routes = web.RouteTableDef()

    if allow_remote:
        log.warning("Allowed remote connection to RPC")

    if hasattr(instance, "on_rpc_server_setup"):
        instance.on_rpc_server_setup(routes, None if not require_authorization else secret_key)

    @routes.route('*', "/__rpc__/{path}")
    async def handle(request: web.Request):
        if require_authorization and request.headers.get("X-Secret", "") != secret_key:
            return json_response({"error": "Unauthorized"}, status=401)

        data = None
        if request.method == "POST":
            data = await request.json()
        return await _handle_rpc_call(instance, request, data)

    @routes.get("/__rpc__/ping")
    def ping(_):
        return web.Response(text="pong")

    app = web.Application()
    app.add_routes(routes)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    server = aiohttp.web.TCPSite(runner, host=host, port=_PORT)
    await server.start()
    log.info(f"Started RPC server at{_PORT}")

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        log.info("Stopping server...")
        await server.stop()
