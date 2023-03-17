from openfreebuds.device.huawei.tools import build_table_row, crc16_xmodem


class HuaweiSppPackage:
    def __init__(self, cmd: bytes, parameters: list[tuple[int, bytes | int]] = None):
        """
        Build new package
        """
        assert len(cmd) == 2
        self.command_id = cmd
        self.parameters: dict[int, bytes] = {}

        if parameters is not None:
            for p_type, p_value in parameters:
                if isinstance(p_value, int):
                    p_value = p_value.to_bytes(1, signed=True, byteorder="big")
                self.parameters[p_type] = p_value

    def __str__(self):
        """
        Pretty-print this pacakge contents
        """
        out = build_table_row(12, "COMMAND_ID")
        out += build_table_row(10, "2 bytes")
        out += build_table_row(40, self.command_id.hex(), []) + "\n"

        out += 70 * "=" + "\n"
        for p_type in self.parameters:
            p_value = self.parameters[p_type]
            out += build_table_row(12, f"PARAM {p_type}")
            out += build_table_row(10, f"{len(p_value)} bytes")
            out += build_table_row(40, p_value.hex())

            if all(c < 128 for c in p_value):
                # ASCII string
                out += p_value.decode("ascii")
            out += "\n"
        return out

    def find_param(self, *args, **kwargs):
        """
        Get parameter value by one of provided types
        """
        for p_type in args:
            if p_type in self.parameters:
                return self.parameters[p_type]

        return b""

    def to_bytes(self):
        """
        Convert this package to bytes.
        Used to send them to device
        """
        # Build body (command_id + parameters)
        body = self.command_id
        for p_type in self.parameters:
            p_value = self.parameters[p_type]
            p_type = p_type.to_bytes(1, byteorder="big")
            p_length = len(p_value).to_bytes(1, byteorder="big")
            body += p_type + p_length + p_value

        # Build package
        result = b"Z" + (len(body) + 1).to_bytes(2, byteorder="big") + b"\x00" + body
        result += crc16_xmodem(result)
        return result

    @staticmethod
    def from_bytes(data: bytes):
        """
        Create Package from bytes.
        Used to parse incoming data.
        """
        assert data[0] == 90
        assert data[3] == 0

        length = int.from_bytes(data[1:3], byteorder="big")

        command_id = data[4:6]
        package = HuaweiSppPackage(command_id)

        position = 6
        while position < length + 3:
            p_type = data[position]
            p_length = data[position + 1]
            p_value = data[position + 2:position + p_length + 2]
            package.parameters[p_type] = p_value
            position += p_length + 2

        return package
