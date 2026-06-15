from framework.api.synthetic_journeys import (
    retrieve_patient_demographics,
    retrieve_patient_demographics_with_missing_last_name,
)


def search_patient():

    return {
        "success": True,
        "patientId": "12345"
    }


def open_patient_chart():

    return {
        "success": True
    }


def provider_open_patient_chart():

    search = search_patient()

    if not search["success"]:
        return {
            "success": False,
            "failed_step": "search"
        }

    demographics = retrieve_patient_demographics()

    if not demographics["success"]:
        return {
            "success": False,
            "failed_step": "demographics"
        }

    chart = open_patient_chart()

    if not chart["success"]:
        return {
            "success": False,
            "failed_step": "chart"
        }

    return {
        "success": True,
        "workflow":
        "Provider Open Patient Chart"
    }

def provider_open_patient_chart_with_failed_search():

    search = {
        "success": False,
        "reason": "Patient search failed"
    }

    if not search["success"]:
        return {
            "success": False,
            "workflow": "Provider Open Patient Chart",
            "failed_step": "search",
            "failure_reason": search["reason"]
        }
def provider_open_patient_chart_with_invalid_demographics():

    search = search_patient()

    if not search["success"]:
        return {
            "success": False,
            "workflow": "Provider Open Patient Chart",
            "failed_step": "search",
            "failure_reason": "Patient search failed",
        }

    demographics = retrieve_patient_demographics_with_missing_last_name()

    if not demographics["success"]:
        return {
            "success": False,
            "workflow": "Provider Open Patient Chart",
            "failed_step": "demographics",
            "failure_reason": "Demographics contract validation failed",
            "missing_fields": demographics["contract"]["missing_fields"],
        }

    chart = open_patient_chart()

    if not chart["success"]:
        return {
            "success": False,
            "workflow": "Provider Open Patient Chart",
            "failed_step": "chart",
            "failure_reason": "Patient chart failed to open",
        }

    return {
        "success": True,
        "workflow": "Provider Open Patient Chart",
    }
