from framework.core.logger import get_logger


def test_logging():

    logger = get_logger()

    logger.info("Framework logging test executed")

    assert True