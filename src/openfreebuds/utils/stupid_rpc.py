import asyncio
import json
import logging
import traceback

import aiohttp
from aiohttp import web

_PORT = 19823


class RemoteError(Exception):
    def __init__(self, data):
        super().__init__(data)
        self.rpc_error_name = data["class"]
        self.rpc_trace = data["trace"]
        self.args = data["args"]

    def __str__(self):
        return f"Got server-side error:\n\n{self.rpc_trace}"


def rpc(func):
    async def _inner(self, *args, **kwargs):
        if self.role == "client":
            return await do_rpc_request(func.__name__, *args, **kwargs)
        return await func(self, *args, **kwargs)

    return _inner


async def do_rpc_request(func, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://127.0.0.1:{_PORT}/{func}",
                data=json.dumps({
                    "args": args,
                    "kwargs": kwargs,
                }),
                headers={
                    "Content-Type": "application/json"
                }
        ) as resp:
            data = json.loads(await resp.text())
            if resp.status == 500:
                raise RemoteError(data)
            return data


async def test_online():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://127.0.0.1:{_PORT}/ping") as resp:
            assert resp.status == 200


# noinspection PyBroadException
async def _handle_rpc_call(instance, static_folder, request: web.Request, data=None):
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


async def run_rpc_server(instance, static_folder):
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

    routes = web.RouteTableDef()

    @routes.route('*', "/{path}")
    async def handle(request: web.Request):
        data = None
        if request.method == "POST":
            data = await request.json()
        return await _handle_rpc_call(instance, static_folder, request, data)

    @routes.get("/ping")
    def ping():
        return web.Response(text="pong")

    app = web.Application()
    app.add_routes(routes)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    server = aiohttp.web.TCPSite(runner, port=_PORT)
    await server.start()

    await asyncio.Event().wait()
