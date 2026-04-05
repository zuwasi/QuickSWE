import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rate_limiter import TokenBucket


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestTokenBucketBasics:
    """Tests for basic token bucket operations that already work."""

    def test_initial_tokens_equal_capacity(self):
        bucket = TokenBucket(10, 1.0)
        assert bucket.tokens == 10.0

    def test_consume_reduces_tokens(self):
        bucket = TokenBucket(10, 1.0)
        assert bucket.consume(3) is True
        assert bucket.tokens <= 7.0 + 0.1  # small timing tolerance

    def test_consume_fails_when_empty(self):
        bucket = TokenBucket(5, 1.0)
        bucket.force_set_tokens(0)
        assert bucket.consume(1) is False


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestTokenBucketCapacityCap:
    """Tests for capacity enforcement — tokens should never exceed capacity."""

    @pytest.mark.fail_to_pass
    def test_refill_does_not_exceed_capacity(self):
        """After a large elapsed time, tokens should cap at capacity."""
        bucket = TokenBucket(10, 100.0)
        bucket.force_set_tokens(0)
        import time
        time.sleep(0.2)  # 0.2s * 100 tokens/s = 20 tokens, but cap is 10
        bucket.refill()
        assert bucket.tokens <= bucket.capacity, (
            f"Tokens ({bucket.tokens}) exceeded capacity ({bucket.capacity})"
        )

    @pytest.mark.fail_to_pass
    def test_consume_after_long_idle_respects_capacity(self):
        """Even after long idle, should not be able to consume > capacity."""
        bucket = TokenBucket(5, 50.0)
        bucket.force_set_tokens(0)
        import time
        time.sleep(0.2)  # would add 10 tokens uncapped
        result = bucket.consume(5)
        assert result is True
        remaining = bucket.tokens
        assert remaining <= 0.1, (
            f"After consuming capacity tokens, remaining ({remaining}) should be ~0"
        )

    @pytest.mark.fail_to_pass
    def test_token_count_capped_after_multiple_refills(self):
        """Multiple refills should not accumulate past capacity."""
        bucket = TokenBucket(10, 50.0)
        import time
        for _ in range(5):
            time.sleep(0.05)
            bucket.refill()
        assert bucket.tokens <= bucket.capacity, (
            f"After multiple refills, tokens ({bucket.tokens}) should not exceed "
            f"capacity ({bucket.capacity})"
        )
