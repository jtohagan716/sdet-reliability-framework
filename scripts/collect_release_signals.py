import time

import requests

from scripts.quality_signal import QualitySignal


# Toggle individual checks here for controlled failure testing.
FAIL_INJECTION = {
    "API Health": False,
    "Metrics Endpoint": False,
    "Prometheus API": False,
}


def check_url(
    name: str,
    url: str,
    retries: int = 3,
    delay_seconds: int = 2,
) -> QualitySignal:

    # Controlled failure injection for testing the release engine.
    if FAIL_INJECTION.get(name, False):
        return QualitySignal(
            name=name,
            status="FAIL",
            category="Runtime Health",
        )

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return QualitySignal(
                    name=name,
                    status="PASS",
                    category="Runtime Health",
                )

            print(f"{name} attempt {attempt}: HTTP {response.status_code}")

        except requests.RequestException as error:
            print(f"{name} attempt {attempt}: {error}")

        time.sleep(delay_seconds)

    return QualitySignal(
        name=name,
        status="FAIL",
        category="Runtime Health",
    )


def collect_release_signals() -> list[QualitySignal]:
    return [
        check_url("API Health", "http://127.0.0.1:8000/health"),
        check_url("Metrics Endpoint", "http://127.0.0.1:8000/metrics"),
        check_url("Prometheus API", "http://127.0.0.1:9090/-/ready"),
    ]


if __name__ == "__main__":
    for signal in collect_release_signals():
        print(signal)