from mutator.helper.decorator import Mutate
import mutator.helper.decorator
import mutator.helper

@Mutate
def some_func():
    pass

@mutator.helper.decorator.Mutate
def foo():
    pass

@mutator.helper.Mutate
def bar():
    pass
