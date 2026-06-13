from framework.reliability.transaction_statistics import TransactionStatistics


def test_transaction_statistics():
    stats = TransactionStatistics()

    results = stats.calculate(
        [
            203,
            315,
            288,
            412,
            390,
        ]
    )

    assert results["count"] == 5
    assert results["minimum"] == 203
    assert results["maximum"] == 412
    assert results["average"] == 321.6
    assert results["p95"] == 412