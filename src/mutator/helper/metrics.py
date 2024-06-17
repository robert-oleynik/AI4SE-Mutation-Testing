def strloc(source: str) -> int:
    return len(source.splitlines())


def locfrac(source: str, mutation: str) -> float:
    return strloc(mutation) / strloc(source)


def dstrloc(source: str, mutation: str) -> int:
    return strloc(mutation) - strloc(source)
