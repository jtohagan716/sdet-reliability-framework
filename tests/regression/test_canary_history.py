from framework.reliability.canary_history import CanaryHistory


def test_canary_history_statistics():

    history = CanaryHistory()

    history.add_result(300)
    history.add_result(350)
    history.add_result(400)

    assert history.average() == 350
    assert history.minimum() == 300
    assert history.maximum() == 400
    assert history.latest() == 400