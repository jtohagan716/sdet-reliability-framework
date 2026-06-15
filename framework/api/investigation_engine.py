INVESTIGATION_GUIDANCE = {
    "PROVIDER_OPEN_PATIENT_CHART_SEARCH_FAILURE": {
        "priority": "HIGH",
        "checks": [
            "Verify patient search service availability.",
            "Verify patient identifier used by the request.",
            "Check whether search failures are isolated or widespread.",
        ],
    },
    "PROVIDER_OPEN_PATIENT_CHART_DEMOGRAPHICS_FAILURE": {
        "priority": "HIGH",
        "checks": [
            "Verify demographics contract validation results.",
            "Check for missing required patient demographics fields.",
            "Verify upstream patient database or demographics service health.",
        ],
    },
    "PROVIDER_OPEN_PATIENT_CHART_CHART_FAILURE": {
        "priority": "MEDIUM",
        "checks": [
            "Verify chart service availability.",
            "Verify provider permissions.",
            "Check whether chart failures are isolated to one patient or widespread.",
        ],
    },
}


def investigate_failure(failure_signature: str) -> dict:
    return INVESTIGATION_GUIDANCE.get(
        failure_signature,
        {
            "priority": "UNKNOWN",
            "checks": [
                "No investigation guidance available for this failure signature.",
            ],
        },
    )