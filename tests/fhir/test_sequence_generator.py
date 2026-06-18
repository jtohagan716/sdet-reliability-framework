from framework.fhir.sequence_generator import SequenceGenerator


def test_sequence_generator_returns_first_value():

    generator = SequenceGenerator(
        prefix="ENC",
        start=1,
    )

    result = generator.next()

    assert result == "ENC000001"


def test_sequence_generator_increments_values():

    generator = SequenceGenerator(
        prefix="ENC",
        start=1,
    )

    first_result = generator.next()
    second_result = generator.next()
    third_result = generator.next()

    assert first_result == "ENC000001"
    assert second_result == "ENC000002"
    assert third_result == "ENC000003"


def test_sequence_generator_supports_custom_start_value():

    generator = SequenceGenerator(
        prefix="APT",
        start=100,
    )

    result = generator.next()

    assert result == "APT000100"


def test_sequence_generator_supports_custom_padding():

    generator = SequenceGenerator(
        prefix="ENC",
        start=1,
        padding=4,
    )

    result = generator.next()

    assert result == "ENC0001"