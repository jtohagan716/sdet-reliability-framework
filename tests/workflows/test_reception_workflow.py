from framework.workflows.reception_workflow import execute_reception_workflow


def test_reception_workflow_executes_successfully():

    result = execute_reception_workflow()

    assert result["status"] == "SUCCESS"
    assert result["workflow"] == "Reception Check-In"


def test_reception_workflow_creates_security_context():

    result = execute_reception_workflow()

    assert (
        result["securityContext"]["userId"]
        == "RECEPTION01"
    )

    assert (
        result["securityContext"]["facilityNcid"]
        == "1048021"
    )


def test_reception_workflow_generates_transaction():

    result = execute_reception_workflow()

    assert (
        result["transaction"]["transactionType"]
        == "PATIENT_CHECK_IN"
    )

def test_reception_workflow_transports_transaction_successfully():
    result = execute_reception_workflow()
    assert result["transportResult"]["transportStatus"] == "SUCCESS"
    assert result["transportResult"]["integrityVerified"] is True