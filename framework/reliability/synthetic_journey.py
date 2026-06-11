from dataclasses import dataclass


@dataclass
class SyntheticStep:
    name: str
    action: str
    expected_result: str


@dataclass
class SyntheticJourney:
    name: str
    role: str
    description: str
    steps: list[SyntheticStep]
    signal_source: str

    def step_count(self):
        return len(self.steps)