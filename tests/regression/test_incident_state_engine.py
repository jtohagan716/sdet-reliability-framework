from framework.reliability.incident_state_engine import (
    determine_incident_state,
)


def test_enterprise_incident():

    incident = determine_incident_state(
        enterprise_wide=True,
        single_mtf=False,
        single_provider=False,
        slow_component="CDR",
    )

    assert incident.scope == "ENTERPRISE"
    assert incident.severity == "HIGH"
    assert incident.primary_owner == "CENTRAL_INFRASTRUCTURE"


def test_provider_incident():

    incident = determine_incident_state(
        enterprise_wide=False,
        single_mtf=False,
        single_provider=True,
        slow_component="CLIENT",
    )

    assert incident.scope == "PROVIDER"
    assert incident.severity == "LOW"
    assert incident.primary_owner == "CLIENT_SUPPORT"