def to_fixed(string, length):
    return string + " " * max(0, length - len(string))
