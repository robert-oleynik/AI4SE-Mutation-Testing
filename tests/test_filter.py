from mutator.helper.pattern import Filter


def test_basic():
    filter = Filter(["foo.app:bar"])
    assert filter.include[0].matches("foo.app", "bar")
    assert filter.should_include("foo.app", "bar")


def test_glob():
    filter = Filter(["foo.app:*"])
    assert filter.include[0].matches("foo.app", "bar")
    assert filter.include[0].matches("foo.app", "main")
    assert filter.should_include("foo.app", "bar")
    assert filter.should_include("foo.app", "main")


def test_exclude():
    filter = Filter(["foo.app:*", "!foo.app:main"])
    assert filter.include[0].matches("foo.app", "bar")
    assert filter.exclude[0].matches("foo.app", "main")
    assert filter.should_include("foo.app", "bar")
    assert not filter.should_include("foo.app", "main")
