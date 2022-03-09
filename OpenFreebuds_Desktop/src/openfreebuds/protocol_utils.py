def build_spp_bytes(data):
    out = b"Z"
    out += (len(data) + 1).to_bytes(2, byteorder="big") + b"\x00"
    out += array2bytes(data)

    checksum = crc16char(out)
    out += (checksum >> 8).to_bytes(1, "big")
    out += (checksum & 0b11111111).to_bytes(1, "big")

    return out


def crc16char(data: bytes):
    # This CRC table extracted from original app
    # I don't know how it works...

    crc16_tab = [0, 4129, 8258, 12387, 16516, 20645, 24774, 28903, -32504, -28375, -24246, -20117, -15988, -11859,
                 -7730,
                 -3601, 4657, 528, 12915, 8786, 21173, 17044, 29431, 25302, -27847, -31976, -19589, -23718, -11331,
                 -15460, -3073, -7202, 9314, 13379, 1056, 5121, 25830, 29895, 17572, 21637, -23190, -19125, -31448,
                 -27383, -6674, -2609, -14932, -10867, 13907, 9842, 5649, 1584, 30423, 26358, 22165, 18100, -18597,
                 -22662, -26855, -30920, -2081, -6146, -10339, -14404, 18628, 22757, 26758, 30887, 2112, 6241, 10242,
                 14371, -13876, -9747, -5746, -1617, -30392, -26263, -22262, -18133, 23285, 19156, 31415, 27286, 6769,
                 2640, 14899, 10770, -9219, -13348, -1089, -5218, -25735, -29864, -17605, -21734, 27814, 31879, 19684,
                 23749, 11298, 15363, 3168, 7233, -4690, -625, -12820, -8755, -21206, -17141, -29336, -25271, 32407,
                 28342, 24277, 20212, 15891, 11826, 7761, 3696, -97, -4162, -8227, -12292, -16613, -20678, -24743,
                 -28808, -28280, -32343, -20022, -24085, -12020, -16083, -3762, -7825, 4224, 161, 12482, 8419, 20484,
                 16421, 28742, 24679, -31815, -27752, -23557, -19494, -15555, -11492, -7297, -3234, 689, 4752, 8947,
                 13010, 16949, 21012, 25207, 29270, -18966, -23093, -27224, -31351, -2706, -6833, -10964, -15091, 13538,
                 9411, 5280, 1153, 29798, 25671, 21540, 17413, -22565, -18438, -30823, -26696, -6305, -2178, -14563,
                 -10436, 9939, 14066, 1681, 5808, 26199, 30326, 17941, 22068, -9908, -13971, -1778, -5841, -26168,
                 -30231, -18038, -22101, 22596, 18533, 30726, 26663, 6336, 2273, 14466, 10403, -13443, -9380, -5313,
                 -1250, -29703, -25640, -21573, -17510, 19061, 23124, 27191, 31254, 2801, 6864, 10931, 14994, -722,
                 -4849, -8852, -12979, -16982, -21109, -25112, -29239, 31782, 27655, 23652, 19525, 15522, 11395, 7392,
                 3265, -4321, -194, -12451, -8324, -20581, -16454, -28711, -24584, 28183, 32310, 20053, 24180, 11923,
                 16050, 3793, 7920]

    s = 0
    for byte in data:
        s = crc16_tab[((s >> 8) ^ byte) & 255] ^ (s << 8)
        s = s & 0b1111111111111111  # use only 16 bits

    return s


def bytes2array(data):
    out = []
    for i in range(len(data)):
        out.append(int.from_bytes(data[i:i + 1], "big", signed=True))
    return out


def array2bytes(data):
    b = b""
    for a in data:
        b += a.to_bytes(1, 'big', signed=True)
    return b


class TLVPackage:
    def __init__(self, pkg_type, data):
        self.type = pkg_type
        self.data = data
        self.length = len(data)

    def get_bytes(self):
        return array2bytes(self.data)

    def get_string(self):
        return self.get_bytes().decode("utf8")


class TLVResponse:
    def __init__(self):
        self.contents: list[TLVPackage] = []

    def __iter__(self):
        return self.contents.__iter__()

    def append(self, item):
        self.contents.append(item)

    def find_by_type(self, type_key):
        for a in self.contents:
            if a.type == type_key:
                return a
        return TLVPackage(type_key, [])

    def find_by_types(self, types_list):
        for a in self.contents:
            if a.type in types_list:
                return a
        return TLVPackage(types_list[0], [])


class TLVException(Exception):
    pass


def parse_tlv(data: bytes) -> TLVResponse:
    data = bytes2array(data)
    response = TLVResponse()
    i = 0

    while i <= len(data) - 2:
        b_cur = data[i]
        b_next = data[i + 1]
        if (b_next & 128) != 0:
            b_post = data[i + 2]
            length = ((b_next & 127) << 7) + (b_post & 127)
            pos = i + 3
        else:
            length = b_next & 127
            pos = i + 2
        i = pos + length
        if length != 0:
            if i > len(data):
                raise TLVException("TLV Package overflow")
            arr = data[pos:pos + length]
            response.append(TLVPackage(b_cur, arr))
        else:
            response.append(TLVPackage(b_cur, []))

    return response
