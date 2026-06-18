class SequenceGenerator:
    def __init__(self, prefix: str, start: int = 1, padding: int = 6):
        self.prefix = prefix
        self.current_value = start
        self.padding = padding

    def next(self) -> str:
        sequence_value = f"{self.prefix}{self.current_value:0{self.padding}d}"
        self.current_value += 1

        return sequence_value