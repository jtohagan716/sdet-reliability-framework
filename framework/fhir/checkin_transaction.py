from framework.fhir.sequence_generator import SequenceGenerator


def process_checkin_transaction(
    appointment: dict,
    encounter_sequence: SequenceGenerator,
) -> dict:
    errors = []

    appointment_id = appointment.get("id")
    appointment_status = appointment.get("status")

    if not appointment_id:
        errors.append("appointment id is required")

    if appointment_status not in ["booked", "arrived", "checked-in"]:
        errors.append("appointment is not eligible for check-in transaction")

    if errors:
        return {
            "success": False,
            "errors": errors,
        }

    encounter_id = encounter_sequence.next()

    return {
        "success": True,
        "appointmentId": appointment_id,
        "appointmentStatus": "checked-in",
        "encounterId": encounter_id,
        "encounterStatus": "in-progress",
        "errors": [],
    }