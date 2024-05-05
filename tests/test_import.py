import mutator.helper
import mutator.helper.decorator
from mutator.helper.decorator import Mutate


@Mutate
def some_func():
    pass

@DeprecationWarning
@Mutate
def some_other_func():
    pass

@mutator.helper.decorator.Mutate
def foo():
    pass

class Foo:
    @mutator.helper.Mutate
    def bar():
        pass

def test_foo():
    assert False
