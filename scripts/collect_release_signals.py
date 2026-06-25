import time
import requests


def check_url(name: str, url: str, retries: int = 3, delay_seconds: int = 2) -> tuple[str, str]:
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return name, "PASS"

            print(f"{name} attempt {attempt}: HTTP {response.status_code}")

        except requests.RequestException as error:
            print(f"{name} attempt {attempt}: {error}")

        time.sleep(delay_seconds)

    return name, "FAIL"


def collect_release_signals() -> list[tuple[str, str]]:
    return [
        check_url("API Health", "http://127.0.0.1:8000/health"),
        check_url("Metrics Endpoint", "http://127.0.0.1:8000/metrics"),
        check_url("Prometheus API", "http://127.0.0.1:9090/-/ready"),
    ]


if __name__ == "__main__":
    signals = collect_release_signals()

    for name, status in signals:
        print(f"{name:<28} {status}")