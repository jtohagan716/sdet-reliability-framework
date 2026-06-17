CHECK_IN_ALLOWED_STATUSES = ["booked", "arrived"]


def check_in_appointment(appointment: dict) -> dict:
    current_status = appointment.get("status")

    if current_status not in CHECK_IN_ALLOWED_STATUSES:
        return {
            "valid": False,
            "errors": [
                f"Appointment with status '{current_status}' cannot be checked in"
            ],
        }

    updated_appointment = appointment.copy()
    updated_appointment["status"] = "checked-in"

    return {
        "valid": True,
        "appointment": updated_appointment,
        "errors": [],
    }