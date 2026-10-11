"""重复付费守护（M14.6-F01：指纹命中即复用，重复付费调用 = 0，NFR-01）。"""


def is_duplicate(seen_fingerprints, fingerprint):
    return fingerprint in seen_fingerprints


def register_fingerprint(seen, fingerprint):
    """登记指纹；重复返回 False（不得重复付费）。"""
    if fingerprint in seen:
        return False
    seen.add(fingerprint)
    return True
