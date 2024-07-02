class LLMStats:
    def __init__(self):
        self.generate_count = 0
        self.input_too_long_count = 0
        self.input_token_count = 0
        self.output_token_count = 0
        self.out_of_memory_count = 0

    def to_dict(self) -> dict:
        return dict(self.__dict__)
