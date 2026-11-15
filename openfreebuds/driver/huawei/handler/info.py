from contextlib import suppress

from openfreebuds.driver.huawei.device_catalog import (
    describe_color,
    describe_model,
    internal_name,
    product_id,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage

BINARY_FIELDS = {27, 32, 34, 33}


class OfbHuaweiInfoHandler(OfbDriverHandlerHuawei):
    """
    Device info handler
    """

    handler_id = "device_info"
    commands = [b"\x01\x07"]

    descriptor = {
        3: "hardware_ver",
        7: "software_ver",
        9: "serial_number",
        10: "device_submodel",
        15: "device_model",
    }

    async def on_init(self):
        # Try to fetch so much props as we can
        resp = await self.driver.send_package(
            HuaweiSppPackage.read_rq(b"\x01\x07", list(range(32)))
        )
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        out = {}
        model_code = None
        if 2 in package.parameters:
            model_code = _as_code(package.parameters[2], 6)
            out["_model_id"] = model_code
            out["_internal_name"] = internal_name(model_code) or ""
            out["_product_id"] = product_id(model_code) or ""

        for key, value in package.parameters.items():
            if key == 2:
                out["field_2"] = describe_model(model_code) or model_code
                continue
            if key == 25:
                color_code = _as_code(value, 2)
                color_name = describe_color(model_code, color_code) if model_code else None
                out["field_25"] = color_name or color_code
                continue
            if key in BINARY_FIELDS:
                # Binary data, no text decoding possible
                out[self.descriptor.get(key, f"field_{key}")] = value.hex()
                continue
            if key == 24 and value[0:2] == b"L-":
                # Per-earphone serial numbers
                _parse_per_earphone_sn(out, value.decode("utf8", "ignore"))
                continue
            out[self.descriptor.get(key, f"field_{key}")] = _decode_text(value)
        await self.driver.put_property("info", None, out)


def _as_code(data: bytes, width: int) -> str:
    """
    Normalize a short model/color identifier: ASCII if printable, hex otherwise.
    """
    text = data.decode("ascii", "ignore").strip("\x00 ")
    if text and text.isalnum():
        return text.upper().zfill(width)
    return data.hex().upper().zfill(width)


def _decode_text(data: bytes) -> str:
    for encoding in ("utf8", "gbk", "gb2312", "ascii"):
        with suppress(UnicodeDecodeError):
            return data.decode(encoding)
    # If all decodings fail, use hex representation
    return data.hex()


def _parse_per_earphone_sn(out, data: str):
    with suppress(Exception):
        left, right = data.split(",")
        out["left_serial_number"] = left[2:]
        out["right_serial_number"] = right[2:]
