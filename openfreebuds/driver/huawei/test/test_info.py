import pytest

from openfreebuds.driver.huawei.constants import CMD_DEVICE_INFO
from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler.info import OfbHuaweiInfoHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


@pytest.mark.asyncio
async def test_pro_5_device_info_response_is_decoded_for_about_page():
    driver = OfbDriverHuaweiGeneric("c0:da:5e:75:c1:08")
    handler = OfbHuaweiInfoHandler()
    handler.driver = driver

    await handler.on_package(HuaweiSppPackage(CMD_DEVICE_INFO, [
        (2, b"\x01\x6b"),
        (3, b"HL1SAKM_Ver.A"),
        (7, b"HarmonyOS 6.1.0.272(F003H003C90)"),
        (9, b"5SPXC26124014696"),
        (10, b"BTFT0023-00016B"),
        (15, b"BTFT0023"),
        (24, b"L-XC8811261A006173,R-XC88332616005030"),
        (25, b"\x07"),
        (27, bytes.fromhex("d1455b017ed0")),
        (29, bytes.fromhex("b611a0240100")),
        (30, bytes.fromhex("4ad49b240100")),
        (32, bytes.fromhex("08c1755edac0")),
        (33, b"\x01"),
        (28, b"MEUCIAjS+h1EC/JOS+eTcxW9VOeabeuzxoWIAxTEKOMgPnNsAiEAzn5Ex+v3Os9DiZEFJm3v1qVg9yYw7SOabt/QJh5/AHw="),
    ]))

    info = await driver.get_property("info", None)

    assert list(info) == [
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
    assert info["manufacturer"] == "Huawei"
    assert info["model"] == "T0023/T0023C"
    assert info["product_id"] == "00016B"
    assert info["device_model"] == "BTFT0023"
    assert info["device_model_full"] == "BTFT0023-00016B"
    assert info["software_ver"] == "HarmonyOS 6.1.0.272"
    assert info["software_build"] == "F003H003C90"
    assert info["hardware_ver"] == "HL1SAKM_Ver.A"
    assert info["serial_number"] == "5SPXC26124014696"
    assert info["left_serial_number"] == "XC8811261A006173"
    assert info["right_serial_number"] == "XC88332616005030"
    assert info["device_submodel"] == "07"
    assert info["device_mac"] == "d0:7e:01:5b:45:d1"
    assert info["bluetooth_address"] == "c0:da:5e:75:c1:08"