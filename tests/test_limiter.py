from mutator.ai.limiter.function import FunctionLimiter


def test_function_limiter_incomplete_docstring():
    source = '''
    class C:
        def app_context(self) -> AppContext:
            """

            :'''
    limiter = FunctionLimiter()
    assert limiter.extract_result(source) is None


def test_function_limiter_incomplete_assignment():
    source = """
    class C:
        def app_context(self) -> AppContext:
            ctx ="""
    limiter = FunctionLimiter()
    assert limiter.extract_result(source) is None
