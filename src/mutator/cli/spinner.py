class Spinner:
    def __init__(self):
        self.spinner = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.i = 0

    def next(self):
        self.i = (self.i + 1) % 8

    def __str__(self) -> str:
        return self.spinner[self.i]
