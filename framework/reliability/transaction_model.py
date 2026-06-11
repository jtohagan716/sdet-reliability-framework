from dataclasses import dataclass


@dataclass
class TransactionVariant:
    name: str
    workload_profile: str
    expected_volume: str
    baseline_ms: float


@dataclass
class TransactionDefinition:
    name: str
    description: str
    variants: list[TransactionVariant]

    def get_variant(self, variant_name: str):
        for variant in self.variants:
            if variant.name == variant_name:
                return variant

        raise ValueError(f"Unknown transaction variant: {variant_name}")