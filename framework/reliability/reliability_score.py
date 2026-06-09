from dataclasses import dataclass


@dataclass
class ReliabilityScore:
    score: float
    verdict: str
    breakdown: dict


def calculate_reliability_score(result: dict, trend: str) -> ReliabilityScore:
    """
    Converts performance telemetry into a single reliability score (0–100).
    """

    avg = result["avg_ms"]
    p95 = result["p95_ms"]
    p99 = result["p99_ms"]
    stdev = result["stdev_ms"]

    score = 100

    breakdown = {}

    # -------------------------
    # 1. P95 PENALTY (MOST IMPORTANT)
    # -------------------------
    p95_penalty = max(0, (p95 - avg) / avg) * 40
    score -= p95_penalty
    breakdown["p95_penalty"] = p95_penalty

    # -------------------------
    # 2. P99 PENALTY (TAIL RISK)
    # -------------------------
    p99_penalty = max(0, (p99 - p95) / p95) * 25
    score -= p99_penalty
    breakdown["p99_penalty"] = p99_penalty

    # -------------------------
    # 3. STABILITY PENALTY
    # -------------------------
    stdev_penalty = (stdev / avg) * 20
    score -= stdev_penalty
    breakdown["stdev_penalty"] = stdev_penalty

    # -------------------------
    # 4. TREND ADJUSTMENT
    # -------------------------
    if trend == "DEGRADING":
        score -= 20
        breakdown["trend_penalty"] = 20
    elif trend == "IMPROVING":
        score += 5
        breakdown["trend_bonus"] = 5
    else:
        breakdown["trend_penalty"] = 0

    # -------------------------
    # FINAL BOUNDS
    # -------------------------
    score = max(0, min(100, score))

    # -------------------------
    # VERDICT
    # -------------------------
    if score >= 85:
        verdict = "PRODUCTION_READY"
    elif score >= 70:
        verdict = "ACCEPTABLE_RISK"
    elif score >= 50:
        verdict = "RISKY"
    else:
        verdict = "FAIL_RELEASE"

    return ReliabilityScore(
        score=round(score, 2),
        verdict=verdict,
        breakdown=breakdown,
    )