import time
import statistics
import requests
from typing import Dict, List


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
        "stdev_ms": round(statistics.stdev(results), 2) if len(results) > 1 else 0.0,
    }