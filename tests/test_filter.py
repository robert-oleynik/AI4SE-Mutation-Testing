from mutator.source import Filter

def test_basic():
    filter = Filter(["foo.app:bar"])
    assert filter.include[0].match("foo.app", "bar")
    assert filter.match("foo.app", "bar")

def test_glob():
    filter = Filter(["foo.app:*"])
    assert filter.include[0].match("foo.app", "bar")
    assert filter.include[0].match("foo.app", "main")
    assert filter.match("foo.app", "bar")
    assert filter.match("foo.app", "main")

def test_exclude():
    filter = Filter(["foo.app:*", "!foo.app:main"])
    assert filter.include[0].match("foo.app", "bar")
    assert filter.exclude[0].match("foo.app", "main")
    assert filter.match("foo.app", "bar")
    assert not filter.match("foo.app", "main")
