from framework.core.config import load_config


def test_load_config():
    config = load_config()

    assert config["environment"] == "dev"
    assert "application" in config