def calculate_release_risk(result: dict) -> dict:

    score = result.get("reliability_score", 0)

    regression = result.get("regression")

    trend = result.get("trend")

    stdev = result.get("stdev_ms", 0)

    risk_points = 0

    # Reliability score

    if score < 90:
        risk_points += 2

    if score < 80:
        risk_points += 3

    # Regression

    if regression == "REGRESSION":
        risk_points += 5

    # Trend

    if trend == "DEGRADING":
        risk_points += 3

    # Stability

    if stdev > 50:
        risk_points += 2

    # Classification

    if risk_points >= 8:
        level = "HIGH"

    elif risk_points >= 4:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "risk_points": risk_points,
        "risk_level": level
    }