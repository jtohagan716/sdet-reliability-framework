from framework.reliability.synthetic_load_generator import SyntheticLoadGenerator


def test_synthetic_load_generator():

    generator = SyntheticLoadGenerator(
        "http://127.0.0.1:8000"
    )

    results = generator.run(
        mode="normal",
        iterations=3,
    )

    assert len(results) == 3

    for latency in results:
        assert 100 <= latency <= 500