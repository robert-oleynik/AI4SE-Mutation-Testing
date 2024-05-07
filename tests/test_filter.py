from mutator.source import Filter

def test_basic():
    filter = Filter("foo.app:bar")
    assert filter.match_module("foo.app")
    assert filter.match_symbol("bar")
