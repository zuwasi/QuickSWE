class APIClient:
    """A simple API client wrapper."""

    def __init__(self):
        pass

    def _execute(self, endpoint):
        """Execute the API call. Override for testing."""
        return {"endpoint": endpoint, "status": "ok"}

    def call(self, endpoint):
        """Make an API call to the given endpoint."""
        return self._execute(endpoint)
