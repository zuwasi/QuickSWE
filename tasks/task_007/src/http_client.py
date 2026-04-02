class SimpleHTTPClient:
    """A simple HTTP client with an overridable request method."""

    def __init__(self):
        pass

    def _do_request(self, url):
        """Perform the actual HTTP request. Override for testing."""
        raise NotImplementedError("Override _do_request in a subclass or mock it")

    def fetch(self, url):
        """Fetch data from the given URL."""
        return self._do_request(url)
