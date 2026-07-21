import pytest

from api_service.database import (
    BACKGROUND_WORKLOAD,
    FOREGROUND_WORKLOAD,
    ISOLATED_POOLS,
    SHARED_POOL,
    get_database_pool_configuration,
    get_database_pool_topology,
)


def test_shared_pool_topology_is_default(monkeypatch):
    monkeypatch.delenv(
        "DATABASE_POOL_TOPOLOGY",
        raising=False,
    )

    assert get_database_pool_topology() == SHARED_POOL


def test_isolated_pool_topology_is_supported(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_POOL_TOPOLOGY",
        ISOLATED_POOLS,
    )

    assert get_database_pool_topology() == ISOLATED_POOLS


def test_unsupported_pool_topology_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_POOL_TOPOLOGY",
        "unlimited_pools",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported DATABASE_POOL_TOPOLOGY",
    ):
        get_database_pool_topology()


def test_foreground_pool_configuration_preserves_existing_defaults(
    monkeypatch,
):
    setting_names = [
        "DB_POOL_MIN_SIZE",
        "DB_POOL_MAX_SIZE",
        "DB_POOL_TIMEOUT_SECONDS",
        "DB_POOL_STARTUP_TIMEOUT_SECONDS",
        "DB_POOL_MAX_WAITING",
    ]

    for setting_name in setting_names:
        monkeypatch.delenv(setting_name, raising=False)

    assert get_database_pool_configuration(
        workload=FOREGROUND_WORKLOAD,
    ) == {
        "min_size": 4,
        "max_size": 8,
        "timeout_seconds": 5.0,
        "startup_timeout_seconds": 30.0,
        "max_waiting": 40,
    }


def test_background_pool_configuration_uses_separate_defaults(
    monkeypatch,
):
    setting_names = [
        "DB_BACKGROUND_POOL_MIN_SIZE",
        "DB_BACKGROUND_POOL_MAX_SIZE",
        "DB_BACKGROUND_POOL_TIMEOUT_SECONDS",
        "DB_BACKGROUND_POOL_STARTUP_TIMEOUT_SECONDS",
        "DB_BACKGROUND_POOL_MAX_WAITING",
    ]

    for setting_name in setting_names:
        monkeypatch.delenv(setting_name, raising=False)

    assert get_database_pool_configuration(
        workload=BACKGROUND_WORKLOAD,
    ) == {
        "min_size": 1,
        "max_size": 2,
        "timeout_seconds": 5.0,
        "startup_timeout_seconds": 30.0,
        "max_waiting": 10,
    }


def test_background_pool_configuration_uses_background_settings(
    monkeypatch,
):
    monkeypatch.setenv("DB_BACKGROUND_POOL_MIN_SIZE", "2")
    monkeypatch.setenv("DB_BACKGROUND_POOL_MAX_SIZE", "3")
    monkeypatch.setenv(
        "DB_BACKGROUND_POOL_TIMEOUT_SECONDS",
        "7.5",
    )
    monkeypatch.setenv(
        "DB_BACKGROUND_POOL_STARTUP_TIMEOUT_SECONDS",
        "45",
    )
    monkeypatch.setenv(
        "DB_BACKGROUND_POOL_MAX_WAITING",
        "12",
    )

    assert get_database_pool_configuration(
        workload=BACKGROUND_WORKLOAD,
    ) == {
        "min_size": 2,
        "max_size": 3,
        "timeout_seconds": 7.5,
        "startup_timeout_seconds": 45.0,
        "max_waiting": 12,
}
