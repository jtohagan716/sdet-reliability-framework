class CanaryHistory:
    def __init__(self):
        self.durations = []

    def add_result(self, duration_ms: float):
        self.durations.append(duration_ms)

    def average(self):
        if not self.durations:
            return 0
        return sum(self.durations) / len(self.durations)

    def minimum(self):
        if not self.durations:
            return 0
        return min(self.durations)

    def maximum(self):
        if not self.durations:
            return 0
        return max(self.durations)

    def latest(self):
        if not self.durations:
            return 0
        return self.durations[-1]