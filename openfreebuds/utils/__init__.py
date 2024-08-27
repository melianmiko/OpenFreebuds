def reverse_dict(obj: dict):
    res = {}
    for a in obj:
        res[obj[a]] = a
    return res
