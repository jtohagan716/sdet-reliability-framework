class LabOrdersClient:
    def __init__(
        self,
        session,
        base_url,
        timeout=5,
    ):
        self._session = session
        self._orders_url = f"{base_url}/api/v1/lab-orders"
        self._timeout = timeout

    def create_order(self, payload):
        return self._session.post(
            self._orders_url,
            json=payload,
            timeout=self._timeout,
        )

    def get_order(self, order_id):
        return self._session.get(
            f"{self._orders_url}/{order_id}",
            timeout=self._timeout,
        )
