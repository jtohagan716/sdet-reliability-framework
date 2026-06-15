def validate_demographics(data):
    required = [
        "patientId",
        "firstName",
        "lastName",
        "dob"
    ]

    for field in required:
        assert field in data


def test_demographics_contract():

    response = {
        "patientId": "12345",
        "firstName": "John",
        "lastName": "Smith",
        "dob": "1970-01-01"
    }

    validate_demographics(response)