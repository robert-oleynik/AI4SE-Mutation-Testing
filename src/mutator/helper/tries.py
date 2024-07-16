import traceback


def tries(num_tries: int, generate) -> list:
    def wrapped():
        try:
            return generate()
        except Exception as e:
            print(traceback.print_exception(e))
            return []

    return [result for _ in range(num_tries) for result in wrapped()]
