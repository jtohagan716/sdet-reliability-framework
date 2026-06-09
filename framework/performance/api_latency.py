import time
import statistics
import requests
from typing import Dict, List


def percentile(data: List[float], percent: float) -> float:
    """
    Simple percentile calculation.

    Example:
    percentile(data, 95)
    """

    if not data:
        return 0.0

    data = sorted(data)

    k = (len(data) - 1) * (percent / 100)

    f = int(k)
    c = min(f + 1, len(data) - 1)

    if f == c:
        return data[int(k)]

    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)

    return d0 + d1


def measure_single_request(url: str, timeout: int = 10) -> float:
    start = time.time()
    requests.get(url, timeout=timeout)
    end = time.time()

    return (end - start) * 1000


def measure_api_latency(url: str, iterations: int = 5) -> Dict:
    """
    PUBLIC CONTRACT FUNCTION

    Returns structured performance telemetry.
    """

    results: List[float] = []

    for _ in range(iterations):
        latency = measure_single_request(url)
        results.append(latency)

    return {
        "url": url,
        "iterations": iterations,
        "min_ms": round(min(results), 2),
        "max_ms": round(max(results), 2),
        "avg_ms": round(statistics.mean(results), 2),
        "stdev_ms": round(
            statistics.stdev(results), 2
        ) if len(results) > 1 else 0.0,

        # Percentiles
        "p50_ms": round(percentile(results, 50), 2),
        "p95_ms": round(percentile(results, 95), 2),
        "p99_ms": round(percentile(results, 99), 2),
    }