from functools import cache

import mutator.helper
import mutator.helper.decorator
from mutator.helper.decorator import Mutate


@Mutate
def some_func(x, y):
    return x + y

@cache
@Mutate
def some_other_func(x, y):
    return x * y

@mutator.helper.decorator.Mutate
def foo(x, y, c):
    if c:
        return some_func(x, y)
    else:
        return some_other_func(x, y)

class Foo:
    @mutator.helper.Mutate
    def bar():
        return 42

def test_foo():
    assert foo(2, 3, False) == 6
    assert foo(2, 3, True) == 5
    assert Foo.bar() == 42
