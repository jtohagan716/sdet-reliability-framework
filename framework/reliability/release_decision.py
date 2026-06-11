def evaluate_release(result: dict):

    score = result.get("reliability_score", 0)

    risk_level = result.get("risk_level", "HIGH")

    status = result.get("status", "FAIL")

    # ---------------------------------
    # HARD STOPS
    # ---------------------------------

    if status.startswith("FAIL"):
        return {
            "decision": "BLOCK_RELEASE",
            "reason": status
        }

    # ---------------------------------
    # RISK-BASED DECISIONS
    # ---------------------------------

    if score >= 95 and risk_level == "LOW":
        return {
            "decision": "APPROVED",
            "reason": "High reliability / Low risk"
        }

    if score >= 80:
        return {
            "decision": "APPROVED_WITH_RISK",
            "reason": "Acceptable reliability"
        }

    if score >= 70:
        return {
            "decision": "REQUIRES_REVIEW",
            "reason": "Engineering review required"
        }

    return {
        "decision": "BLOCK_RELEASE",
        "reason": "Reliability score too low"
    }