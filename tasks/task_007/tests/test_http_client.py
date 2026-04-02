import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.http_client import SimpleHTTPClient


# ──────────────────────────────────────────────
# Helper subclasses
# ──────────────────────────────────────────────

class SuccessClient(SimpleHTTPClient):
    """Always succeeds on _do_request."""
    def _do_request(self, url):
        return {"status": 200, "url": url}


class FailNTimesClient(SimpleHTTPClient):
    """Fails N times then succeeds."""
    def __init__(self, fail_count, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fail_count = fail_count
        self._attempts = 0

    def _do_request(self, url):
        self._attempts += 1
        if self._attempts <= self._fail_count:
            raise ConnectionError(f"Attempt {self._attempts} failed")
        return {"status": 200, "url": url, "attempts": self._attempts}


class AlwaysFailClient(SimpleHTTPClient):
    """Always fails on _do_request."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attempts = 0

    def _do_request(self, url):
        self._attempts += 1
        raise ConnectionError(f"Attempt {self._attempts} failed")


# ──────────────────────────────────────────────
# Pass-to-pass: existing functionality tests
# ──────────────────────────────────────────────

class TestExistingFunctionality:
    def test_fetch_success(self):
        client = SuccessClient()
        result = client.fetch("http://example.com")
        assert result["status"] == 200
        assert result["url"] == "http://example.com"

    def test_fetch_raises_on_failure(self):
        client = SimpleHTTPClient()
        with pytest.raises(NotImplementedError):
            client.fetch("http://example.com")

    def test_do_request_base_raises(self):
        client = SimpleHTTPClient()
        with pytest.raises(NotImplementedError):
            client._do_request("http://example.com")


# ──────────────────────────────────────────────
# Fail-to-pass: retry feature tests
# ──────────────────────────────────────────────

class TestRetryLogic:
    @pytest.mark.fail_to_pass
    def test_max_retries_parameter(self):
        client = SuccessClient(max_retries=5)
        assert client.max_retries == 5

    @pytest.mark.fail_to_pass
    def test_retry_succeeds_after_failures(self):
        client = FailNTimesClient(fail_count=2, max_retries=3, backoff_base=0.01)
        result = client.fetch("http://example.com")
        assert result["status"] == 200
        assert result["attempts"] == 3  # 2 failures + 1 success

    @pytest.mark.fail_to_pass
    def test_retry_exhausted_raises(self):
        client = AlwaysFailClient(max_retries=2, backoff_base=0.01)
        with pytest.raises(ConnectionError):
            client.fetch("http://example.com")
        assert client._attempts == 3  # 1 initial + 2 retries

    @pytest.mark.fail_to_pass
    def test_call_count_tracked(self):
        client = FailNTimesClient(fail_count=1, max_retries=3, backoff_base=0.01)
        client.fetch("http://example.com")
        assert client.call_count == 2  # 1 failure + 1 success

    @pytest.mark.fail_to_pass
    def test_exponential_backoff_timing(self):
        client = FailNTimesClient(fail_count=2, max_retries=3, backoff_base=0.05)
        start = time.time()
        client.fetch("http://example.com")
        elapsed = time.time() - start
        # backoff_base * 2^0 + backoff_base * 2^1 = 0.05 + 0.10 = 0.15
        assert elapsed >= 0.12  # allow small timing tolerance

    @pytest.mark.fail_to_pass
    def test_no_retry_on_success(self):
        client = SuccessClient(max_retries=5, backoff_base=0.01)
        result = client.fetch("http://example.com")
        assert result["status"] == 200
        assert client.call_count == 1
