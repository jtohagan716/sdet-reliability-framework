import pytest

from api_service.database import (
    BOUNDED_POOL,
    CONNECTION_PER_OPERATION,
    get_database_connection_strategy,
    get_database_pool_configuration,
)


def test_bounded_pool_is_default(monkeypatch):
    monkeypatch.delenv(
        "DATABASE_CONNECTION_STRATEGY",
        raising=False,
    )

    assert (
        get_database_connection_strategy()
        == BOUNDED_POOL
    )


def test_bounded_pool_strategy_is_supported(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_CONNECTION_STRATEGY",
        BOUNDED_POOL,
    )

    assert get_database_connection_strategy() == BOUNDED_POOL


def test_unsupported_strategy_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_CONNECTION_STRATEGY",
        "unbounded_pool",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported DATABASE_CONNECTION_STRATEGY",
    ):
        get_database_connection_strategy()


def test_pool_configuration_uses_expected_defaults(monkeypatch):
    setting_names = [
        "DB_POOL_MIN_SIZE",
        "DB_POOL_MAX_SIZE",
        "DB_POOL_TIMEOUT_SECONDS",
        "DB_POOL_STARTUP_TIMEOUT_SECONDS",
        "DB_POOL_MAX_WAITING",
    ]

    for setting_name in setting_names:
        monkeypatch.delenv(setting_name, raising=False)

    assert get_database_pool_configuration() == {
        "min_size": 4,
        "max_size": 8,
        "timeout_seconds": 5.0,
        "startup_timeout_seconds": 30.0,
        "max_waiting": 40,
    }


def test_pool_minimum_cannot_exceed_maximum(monkeypatch):
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "9")
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "8")

    with pytest.raises(
        ValueError,
        match="DB_POOL_MIN_SIZE cannot exceed DB_POOL_MAX_SIZE",
    ):
        get_database_pool_configuration()


def test_pool_size_must_be_positive(monkeypatch):
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "0")

    with pytest.raises(
        ValueError,
        match="DB_POOL_MIN_SIZE must be at least 1",
    ):
        get_database_pool_configuration()
