import sys
import traceback

from openfreebuds.driver.huawei.package import HuaweiSppPackage

while True:
    try:
        data = bytes.fromhex(input("HEX-stream: "))
        if data[0] != b"\x5a":
            data = b"\x5a\x00" + data.split(b"\x5a\x00", 1)[1]

        print("")
        print(f"HEX: {data.hex()}")
        print("")
        print(HuaweiSppPackage.from_bytes(data).to_table_string())
    except Exception:
        traceback.print_exc()
