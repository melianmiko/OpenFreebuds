def format_mac_address(h: str):
    return ':'.join(h[i:i+2] for i in range(0, 12, 2)).upper()
