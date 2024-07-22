def strloc(source: str) -> int:
    return len(source.splitlines())


def locfrac(source: str, mutant: str) -> float:
    return strloc(mutant) / strloc(source)


def dstrloc(source: str, mutant: str) -> int:
    return strloc(mutant) - strloc(source)
