from openfreebuds.driver.huawei.utils import crc16_xmodem, build_table_row
from openfreebuds.exceptions import OfbPackageChecksumError


class HuaweiSppPackage:
    @staticmethod
    def raw(cmd: bytes, payload: bytes, resp: bytes = b""):
        return HuaweiSppPackage(cmd=cmd, resp=resp, raw_payload=payload)

    @staticmethod
    def change_rq(cmd: bytes, parameters: list[tuple[int, bytes | int]]):
        return HuaweiSppPackage(cmd=cmd, resp=cmd, parameters=parameters)

    @staticmethod
    def change_rq_nowait(cmd: bytes, parameters: list[tuple[int, bytes | int]]):
        return HuaweiSppPackage(cmd=cmd, parameters=parameters)

    @staticmethod
    def read_rq(cmd: bytes, parameters: list[int]):
        return HuaweiSppPackage(cmd=cmd,
                                resp=cmd,
                                parameters=[(i, b"") for i in parameters])

    def __init__(
            self,
            cmd: bytes,
            parameters: list[tuple[int, bytes | int]] = None,
            resp: bytes = b"",
            raw_payload: bytes | None = None,
    ):
        """
        Build new package
        """
        assert len(cmd) == 2
        if raw_payload is not None and parameters is not None:
            raise ValueError("Raw Huawei package payload cannot be combined with TLV parameters")
        self.command_id = cmd
        self.response_id = resp
        self.parameters: dict[int, bytes] = {}
        self.raw_payload = raw_payload

        if parameters is not None:
            for p_type, p_value in parameters:
                if isinstance(p_value, int):
                    p_value = p_value.to_bytes(1, signed=True, byteorder="big")
                self.parameters[p_type] = p_value

    def __str__(self):
        out = [f"command={self.command_id.hex()}"]
        if self.raw_payload is not None:
            out.append(f"raw_payload={self.raw_payload}")
            return ", ".join(out)
        for p_type in self.parameters:
            p_value = self.parameters[p_type]
            out.append(f"param_{p_type}={p_value}")
        return ", ".join(out)

    def to_table_string(self):
        """
        Pretty-print this pacakge contents
        """
        if self.raw_payload is not None:
            return (
                build_table_row(12, "COMMAND_ID")
                + build_table_row(10, "2 bytes")
                + build_table_row(40, self.command_id.hex(), [])
                + "\n"
                + build_table_row(12, "RAW")
                + build_table_row(10, f"{len(self.raw_payload)} bytes")
                + build_table_row(max(40, len(self.raw_payload.hex())), self.raw_payload.hex())
                + "\n"
            )

        hex_len = 40
        for p_type in self.parameters:
            cand_l = self.parameters[p_type].hex()
            if len(cand_l) > hex_len:
                hex_len = len(cand_l)

        out = build_table_row(12, "COMMAND_ID")
        out += build_table_row(10, "2 bytes")
        out += build_table_row(hex_len, self.command_id.hex(), []) + "\n"

        out += (30 + hex_len) * "=" + "\n"
        for p_type in self.parameters:
            p_value = self.parameters[p_type]
            out += build_table_row(12, f"PARAM {p_type}")
            out += build_table_row(10, f"{len(p_value)} bytes")
            out += build_table_row(hex_len, p_value.hex())

            if all(c < 128 for c in p_value):
                # ASCII string
                out += p_value.decode("ascii")
            out += "\n"
        return out

    def find_param(self, *args) -> bytes:
        """
        Get parameter value by one of provided types
        """
        for p_type in args:
            if p_type in self.parameters:
                return self.parameters[p_type]

        return b""

    def has_param(self, *args) -> bool:
        """
        Check whether one of provided parameter types is present.
        """
        return any(p_type in self.parameters for p_type in args)

    def error_code(self) -> int | None:
        """
        Huawei replies with param 127 when a command is rejected.
        """
        if not self.has_param(127):
            return None

        return int.from_bytes(self.parameters[127], byteorder="big")

    def is_error_response(self) -> bool:
        return self.error_code() is not None

    def to_bytes(self):
        """
        Convert this package to bytes.
        Used to send them to device
        """
        if self.raw_payload is None:
            # Build body (command_id + parameters)
            body = self.command_id
            for p_type in self.parameters:
                p_value = self.parameters[p_type]
                p_type = p_type.to_bytes(1, byteorder="big")
                p_length = self._encode_param_length(len(p_value))
                body += p_type + p_length + p_value
        else:
            body = self.command_id + self.raw_payload

        # Build package
        result = b"Z" + (len(body) + 1).to_bytes(2, byteorder="big") + b"\x00" + body
        result += crc16_xmodem(result)
        return result

    @staticmethod
    def re_checksum(data: bytes):
        return HuaweiSppPackage.from_bytes(data, validate_checksum=False).to_bytes()

    @staticmethod
    def from_bytes(data: bytes, validate_checksum=False):
        """
        Create Package from bytes.
        Used to parse incoming data.
        """
        assert data[0] == 90
        assert data[3] == 0

        if validate_checksum:
            crc_data = data[0:-2]
            crc_value = data[-2:]
            if crc16_xmodem(crc_data) != crc_value:
                raise OfbPackageChecksumError(f"{crc16_xmodem(crc_data)} != {crc_value}")

        length = int.from_bytes(data[1:3], byteorder="big")

        command_id = data[4:6]
        package = HuaweiSppPackage(command_id)

        position = 6
        while position < length + 3:
            p_type = data[position]
            p_length, length_size = HuaweiSppPackage._decode_param_length(data, position + 1)
            p_value_start = position + 1 + length_size
            p_value = data[p_value_start:p_value_start + p_length]
            package.parameters[p_type] = p_value
            position += p_length + 1 + length_size

        return package

    @staticmethod
    def _encode_param_length(value: int) -> bytes:
        if value < 0x80:
            return value.to_bytes(1, byteorder="big")
        if value > 0x3fff:
            raise ValueError(f"Huawei SPP parameter is too large: {value}")
        return bytes([0x80 | ((value >> 7) & 0x7f), value & 0x7f])

    @staticmethod
    def _decode_param_length(data: bytes, position: int) -> tuple[int, int]:
        first = data[position]
        if first & 0x80:
            return ((first & 0x7f) << 7) | (data[position + 1] & 0x7f), 2
        return first & 0x7f, 1
