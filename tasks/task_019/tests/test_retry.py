import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.retry import retry, MaxRetriesExceededError


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_retry_counter_resets_between_calls():
    """After one invocation exhausts retries, the next must start fresh."""
    call_count = 0

    @retry(max_retries=2, backoff_base=0.001)
    def flaky():
        nonlocal call_count
        call_count += 1
        raise ValueError("boom")

    with pytest.raises(MaxRetriesExceededError):
        flaky()

    first_run_calls = call_count
    call_count = 0

    with pytest.raises(MaxRetriesExceededError):
        flaky()

    assert call_count == 3, (
        f"Second invocation should attempt 3 times (1 + 2 retries), "
        f"got {call_count}"
    )


@pytest.mark.fail_to_pass
def test_success_after_previous_failure():
    """A successful second call must work even if the first failed."""
    attempt = 0

    @retry(max_retries=2, backoff_base=0.001)
    def sometimes_fails(should_fail):
        nonlocal attempt
        attempt += 1
        if should_fail:
            raise ValueError("fail")
        return "ok"

    with pytest.raises(MaxRetriesExceededError):
        sometimes_fails(True)

    result = sometimes_fails(False)
    assert result == "ok"


@pytest.mark.fail_to_pass
def test_independent_retry_budgets():
    """Two separate calls must each get their own full retry budget."""
    counts = {"a": 0, "b": 0}

    @retry(max_retries=3, backoff_base=0.001)
    def record_and_fail(label):
        counts[label] += 1
        raise RuntimeError(f"{label} fails")

    with pytest.raises(MaxRetriesExceededError):
        record_and_fail("a")

    with pytest.raises(MaxRetriesExceededError):
        record_and_fail("b")

    assert counts["a"] == 4, f"Expected 4 attempts for 'a', got {counts['a']}"
    assert counts["b"] == 4, f"Expected 4 attempts for 'b', got {counts['b']}"


# ─── pass_to_pass ───────────────────────────────────────────────

def test_succeeds_without_retry():
    """A function that succeeds immediately should not retry."""
    @retry(max_retries=3, backoff_base=0.001)
    def ok():
        return 42

    assert ok() == 42


def test_succeeds_on_second_attempt():
    """Retry succeeds on the second try."""
    calls = 0

    @retry(max_retries=3, backoff_base=0.001)
    def second_time_charm():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise ValueError("not yet")
        return "done"

    assert second_time_charm() == "done"
    assert calls == 2


def test_on_retry_callback():
    """on_retry callback fires on each retry."""
    log = []

    @retry(max_retries=2, backoff_base=0.001,
           on_retry=lambda a, e, d: log.append(a))
    def fails():
        raise RuntimeError("fail")

    with pytest.raises(MaxRetriesExceededError):
        fails()

    assert log == [1, 2]
