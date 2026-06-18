from framework.security.security_context import SecurityContext
from framework.fhir.sequence_generator import SequenceGenerator
from framework.fhir.checkin_transaction import process_checkin_transaction
from framework.fhir.transaction_reporter import generate_transaction_report
from framework.fhir.transaction_transport import transport_transaction


def execute_reception_workflow():

    security_context = SecurityContext(
        user_id="RECEPTION01",
        facility_ncid="1048021",
        role="Reception",
        permissions=[
            "CHECK_IN",
            "VIEW_APPOINTMENT",
            "CREATE_ENCOUNTER",
        ],
        session_id="SESSION001",
    )

    appointment = {
        "resourceType": "Appointment",
        "id": "APT001",
        "status": "booked",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }

    encounter_sequence = SequenceGenerator(
        prefix="ENC",
        start=1,
    )

    transaction_result = process_checkin_transaction(
        appointment,
        encounter_sequence,
    )

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "facilityNcid": security_context.facility_ncid,
        "appointmentId": transaction_result["appointmentId"],
        "encounterId": transaction_result["encounterId"],
        "userId": security_context.user_id,
        "workstationId": "CLINIC-WS-05",
        "sessionId": security_context.session_id,
        "timestamp": "2026-06-18T09:00:00",
    }
    transport_result = transport_transaction(transaction)
    report = generate_transaction_report(transaction)

    return {
        "workflow": "Reception Check-In",
        "status": "SUCCESS",
        "securityContext": security_context.to_dict(),
        "transaction": transaction,
        "transactionResult": transaction_result,
        "report": report,
        "transportResult": transport_result,
    }

def test_reception_workflow_transports_transaction_successfully():

    result = execute_reception_workflow()

    assert result["transportResult"]["transportStatus"] == "SUCCESS"
    assert result["transportResult"]["integrityVerified"] is True