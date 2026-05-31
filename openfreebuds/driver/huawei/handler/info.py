from contextlib import suppress
import re

from openfreebuds.driver.huawei.constants import CMD_DEVICE_INFO
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiInfoHandler(OfbDriverHandlerHuawei):
    """
    Device info handler
    """

    handler_id = "device_info"
    commands = [CMD_DEVICE_INFO]

    descriptor = {
        1: "bt_version",
        2: "product_id",
        3: "hardware_ver",
        4: "device_phone_number",
        5: "device_bt_mac",
        6: "device_imei",
        7: "software_ver",
        8: "open_source_ver",
        9: "serial_number",
        10: "device_model_full",
        11: "device_emmc_id",
        12: "device_name",
        15: "device_model",
        25: "device_submodel",
        27: "device_mac",
        32: "bluetooth_address",
    }

    internal_fields = {28, 29, 30, 33}

    field_order = [
        "manufacturer",
        "model",
        "product_id",
        "device_model",
        "device_model_full",
        "hardware_ver",
        "software_ver",
        "software_build",
        "serial_number",
        "left_serial_number",
        "right_serial_number",
        "device_submodel",
        "bluetooth_address",
        "device_mac",
    ]

    model_aliases = {
        "BTFT0023": "T0023/T0023C",
    }

    async def on_init(self):
        # Try to fetch so much props as we can
        resp = await self.driver.send_package(
            HuaweiSppPackage.read_rq(CMD_DEVICE_INFO, list(range(32)))
        )
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        out = {"manufacturer": "Huawei"}
        for key in package.parameters:
            if key in self.internal_fields:
                continue

            value = package.parameters[key]
            if key == 24 and (value.startswith(b"L-") or value.startswith(b"R-")):
                # Per-earphone serial numbers
                try:
                    _parse_per_earphone_sn(out, _decode_text(value))
                except:
                    pass
                continue

            field_name = self.descriptor.get(key, f"field_{key}")
            _put_decoded_field(out, field_name, key, value)

        model_id = out.get("device_model", "")
        if model_id in self.model_aliases:
            out["model"] = self.model_aliases[model_id]

        await self.driver.put_property("info", None, _order_fields(out, self.field_order))


def _parse_per_earphone_sn(out, data: str):
    with suppress(Exception):
        for item in data.split(","):
            if item.startswith("L-"):
                out["left_serial_number"] = item[2:].strip()
            elif item.startswith("R-"):
                out["right_serial_number"] = item[2:].strip()


def _put_decoded_field(out: dict, field_name: str, key: int, value: bytes):
    if key == 2:
        out[field_name] = value.hex().upper().zfill(6)
    elif key in (27, 32) and len(value) == 6:
        out[field_name] = _decode_little_endian_mac(value)
    elif key == 7:
        software_ver = _decode_text(value)
        out[field_name] = _strip_build_suffix(software_ver)
        build = _extract_build_suffix(software_ver)
        if build:
            out["software_build"] = build
    elif key == 25 and len(value) == 1:
        out[field_name] = f"{value[0]:02x}"
    else:
        out[field_name] = _decode_text(value)


def _decode_text(value: bytes):
    for encoding in ["utf8", "gbk", "gb2312", "ascii"]:
        try:
            text = value.decode(encoding).strip("\x00").strip()
        except UnicodeDecodeError:
            continue

        if text and all(char.isprintable() for char in text):
            return text

    return value.hex()


def _decode_little_endian_mac(value: bytes):
    return ":".join(f"{item:02x}" for item in reversed(value))


def _strip_build_suffix(value: str):
    return re.sub(r"\([^)]*\)$", "", value).strip()


def _extract_build_suffix(value: str):
    match = re.search(r"\(([^)]*)\)$", value)
    if match is None:
        return ""
    return match.group(1)


def _order_fields(info: dict, order: list[str]):
    out = {}
    for key in order:
        if key in info:
            out[key] = info[key]
    for key, value in info.items():
        if key not in out:
            out[key] = value
    return out
