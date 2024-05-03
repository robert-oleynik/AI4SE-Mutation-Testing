from mutator.helper.decorator import Mutate
import mutator.helper.decorator
import mutator.helper

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
