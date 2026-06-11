from framework.reliability.incident_state import IncidentState


def determine_incident_state(
    enterprise_wide: bool,
    single_mtf: bool,
    single_provider: bool,
    slow_component: str,
):

    if enterprise_wide:

        return IncidentState(
            state="ACTIVE",
            severity="HIGH",
            scope="ENTERPRISE",
            confidence="HIGH",
            primary_owner="CENTRAL_INFRASTRUCTURE",
        )

    if single_mtf:

        return IncidentState(
            state="ACTIVE",
            severity="MEDIUM",
            scope="MTF",
            confidence="HIGH",
            primary_owner="LOCAL_INFRASTRUCTURE",
        )

    if single_provider:

        return IncidentState(
            state="ACTIVE",
            severity="LOW",
            scope="PROVIDER",
            confidence="HIGH",
            primary_owner="CLIENT_SUPPORT",
        )

    return IncidentState(
        state="UNKNOWN",
        severity="UNKNOWN",
        scope="UNKNOWN",
        confidence="LOW",
        primary_owner="FURTHER_ANALYSIS_REQUIRED",
    )