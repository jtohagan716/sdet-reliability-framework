import requests


class SyntheticLoadGenerator:

    def __init__(self, base_url):
        self.base_url = base_url

    def run(
        self,
        mode="normal",
        iterations=5,
    ):

        latencies = []

        for _ in range(iterations):

            response = requests.get(
                f"{self.base_url}/echo?mode={mode}",
                timeout=10,
            )

            data = response.json()

            if "simulated_latency_ms" in data:
                latencies.append(
                    data["simulated_latency_ms"]
                )

        return latencies