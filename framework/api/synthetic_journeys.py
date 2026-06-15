from framework.api.contracts import (
    validate_demographics_contract
)


def retrieve_patient_demographics():

    response = {
        "patientId": "12345",
        "firstName": "John",
        "lastName": "Smith",
        "dob": "1970-01-01"
    }

    contract_result = validate_demographics_contract(
        response
    )

    return {
        "journey": "Retrieve Patient Demographics",
        "success": contract_result["valid"],
        "contract": contract_result,
        "response": response
    }

def retrieve_patient_demographics_with_missing_last_name():

    response = {
        "patientId": "12345",
        "firstName": "John",
        "dob": "1970-01-01"
    }

    contract_result = validate_demographics_contract(
        response
    )

    return {
        "journey": "Retrieve Patient Demographics",
        "success": contract_result["valid"],
        "contract": contract_result,
        "response": response,
        "failure_reason": "Missing required demographics field"
    }

