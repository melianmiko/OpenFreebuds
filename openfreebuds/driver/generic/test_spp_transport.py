from openfreebuds.driver.generic.spp_transport import rfcomm_sockaddr


def test_rfcomm_sockaddr():
    # struct sockaddr_rc: family (u16), bdaddr (6 bytes, reversed), channel (u8), padding
    addr = rfcomm_sockaddr("24:30:F8:C1:27:05", 1)
    assert addr == bytes.fromhex("1f00" "0527c1f83024" "01" "00")
    assert len(addr) == 10
