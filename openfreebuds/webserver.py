from typing import Optional

from aiohttp.web import Request
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_response import json_response
from aiohttp.web_routedef import RouteTableDef

from openfreebuds.constants import APP_ROOT
from openfreebuds.manager.generic import IOpenFreebuds
from openfreebuds.shortcuts import OfbShortcuts
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbWebServer")
STATIC_PATH = APP_ROOT / "openfreebuds" / "assets" / "web_static"


def setup_routes(instance: IOpenFreebuds, routes: RouteTableDef, secret: Optional[str]):
    all_shortcuts = OfbShortcuts.all()

    @routes.get("/")
    def index_html(request: Request):
        if secret is not None and request.headers.get("X-Secret", "") != secret:
            return json_response({"error": "Unauthorized"}, status=401)
        return FileResponse(STATIC_PATH / "index.html")

    @routes.get("/list_shortcuts")
    def list_shortcuts(request: Request):
        if secret is not None and request.headers.get("X-Secret", "") != secret:
            return json_response({"error": "Unauthorized"}, status=401)
        return json_response(all_shortcuts)

    @routes.get("/{shortcut}")
    async def handle_shortcut(request: Request):
        if secret is not None and request.headers.get("X-Secret", "") != secret:
            return json_response({"error": "Unauthorized"}, status=401)

        name = request.match_info["shortcut"]
        if name not in all_shortcuts:
            return json_response({"error": "Not found"}, status=404)

        try:
            await instance.run_shortcut(name)
            return json_response({"result": True})
        except Exception:
            log.exception(f"Wile running {name} shortcut")
            return json_response({"error": "Failed"}, status=500)
