class HealthClient:
    """HTTP client for LabFlow health-check endpoints."""

    def __init__(
        self,
        session,
        base_url,
        timeout=5,
    ):
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def get_liveness(self):
        return self._session.get(
            f"{self._base_url}/health/live",
            timeout=self._timeout,
        )

    def get_readiness(self):
        return self._session.get(
            f"{self._base_url}/health/ready",
            timeout=self._timeout,
        )