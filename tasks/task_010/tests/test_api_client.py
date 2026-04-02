import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api_client import APIClient


# ──────────────────────────────────────────────
# Pass-to-pass: existing functionality tests
# ──────────────────────────────────────────────

class TestExistingFunctionality:
    def test_call_returns_result(self):
        client = APIClient()
        result = client.call("/users")
        assert result["endpoint"] == "/users"
        assert result["status"] == "ok"

    def test_call_different_endpoints(self):
        client = APIClient()
        r1 = client.call("/users")
        r2 = client.call("/posts")
        assert r1["endpoint"] == "/users"
        assert r2["endpoint"] == "/posts"

    def test_execute_override(self):
        class CustomClient(APIClient):
            def _execute(self, endpoint):
                return {"custom": True, "endpoint": endpoint}

        client = CustomClient()
        result = client.call("/test")
        assert result["custom"] is True


# ──────────────────────────────────────────────
# Fail-to-pass: rate limiting feature tests
# ──────────────────────────────────────────────

class TestRateLimiting:
    @pytest.mark.fail_to_pass
    def test_max_calls_per_second_parameter(self):
        client = APIClient(max_calls_per_second=5)
        assert client.max_calls_per_second == 5

    @pytest.mark.fail_to_pass
    def test_default_rate_limit(self):
        client = APIClient(max_calls_per_second=10)
        assert client.max_calls_per_second == 10

    @pytest.mark.fail_to_pass
    def test_rate_limiting_enforced(self):
        # Allow only 5 calls per second
        client = APIClient(max_calls_per_second=5)
        start = time.time()
        # Make 10 calls — should take at least ~1 second due to rate limit
        for i in range(10):
            client.call(f"/endpoint/{i}")
        elapsed = time.time() - start
        # 10 calls at 5/sec should take at least ~1 second
        assert elapsed >= 0.9

    @pytest.mark.fail_to_pass
    def test_rate_limiting_allows_burst_within_limit(self):
        client = APIClient(max_calls_per_second=20)
        start = time.time()
        # Make 10 calls — well within 20/sec, should be fast
        for i in range(10):
            client.call(f"/endpoint/{i}")
        elapsed = time.time() - start
        # Should complete quickly since under the limit
        assert elapsed < 1.0

    @pytest.mark.fail_to_pass
    def test_rate_limited_calls_still_return_results(self):
        client = APIClient(max_calls_per_second=5)
        results = []
        for i in range(6):
            results.append(client.call(f"/ep/{i}"))
        assert len(results) == 6
        assert all(r["status"] == "ok" for r in results)

    @pytest.mark.fail_to_pass
    def test_rate_limit_tight_timing(self):
        # 3 calls per second max
        client = APIClient(max_calls_per_second=3)
        start = time.time()
        for i in range(6):
            client.call(f"/endpoint/{i}")
        elapsed = time.time() - start
        # 6 calls at 3/sec should take at least ~1 second
        assert elapsed >= 0.9
