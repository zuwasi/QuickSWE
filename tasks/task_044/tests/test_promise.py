import sys
import os
import time
import threading
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scheduler import WorkScheduler, WorkItem
from src.executor import TaskExecutor


# ── pass-to-pass: WorkScheduler basic operations ──────────────────────


class TestWorkSchedulerBasic:
    def test_schedule_and_next(self):
        sched = WorkScheduler()
        item = WorkItem(lambda: 42)
        sched.schedule(item)
        got = sched.next(timeout=1)
        assert got is item

    def test_priority_ordering(self):
        sched = WorkScheduler()
        low = WorkItem(lambda: "low", priority=1)
        high = WorkItem(lambda: "high", priority=10)
        sched.schedule(low)
        sched.schedule(high)
        first = sched.next(timeout=1)
        assert first is high

    def test_next_timeout_returns_none(self):
        sched = WorkScheduler()
        result = sched.next(timeout=0.05)
        assert result is None

    def test_work_item_execute(self):
        item = WorkItem(lambda x, y: x + y, args=(3, 4))
        item.execute()
        assert item.result == 7
        assert item.error is None
        assert item.completed.is_set()

    def test_work_item_execute_error(self):
        def bad():
            raise ValueError("boom")
        item = WorkItem(bad)
        item.execute()
        assert item.error is not None
        assert "boom" in str(item.error)

    def test_pending_count(self):
        sched = WorkScheduler()
        assert sched.pending_count == 0
        sched.schedule(WorkItem(lambda: 1))
        sched.schedule(WorkItem(lambda: 2))
        assert sched.pending_count == 2


class TestTaskExecutorBasic:
    def test_submit_returns_future(self):
        with TaskExecutor(max_workers=2) as executor:
            future = executor.submit(lambda: 42)
            assert future.result(timeout=5) == 42

    def test_submit_exception(self):
        with TaskExecutor(max_workers=2) as executor:
            future = executor.submit(lambda: 1 / 0)
            with pytest.raises(ZeroDivisionError):
                future.result(timeout=5)


# ── fail-to-pass: Promise implementation ──────────────────────────


class TestPromiseBasic:
    @pytest.mark.fail_to_pass
    def test_resolve_basic(self):
        """Promise.resolve creates an immediately resolved promise."""
        from src.promise import Promise
        p = Promise.resolve(42)
        assert p.result(timeout=2) == 42

    @pytest.mark.fail_to_pass
    def test_reject_basic(self):
        """Promise.reject creates an immediately rejected promise."""
        from src.promise import Promise
        p = Promise.reject(ValueError("oops"))
        with pytest.raises(ValueError, match="oops"):
            p.result(timeout=2)

    @pytest.mark.fail_to_pass
    def test_executor_fn_called(self):
        """Promise constructor calls executor_fn with resolve and reject."""
        from src.promise import Promise
        called = []
        def executor(resolve, reject):
            called.append(True)
            resolve("done")
        p = Promise(executor)
        assert len(called) == 1
        assert p.result(timeout=2) == "done"

    @pytest.mark.fail_to_pass
    def test_executor_fn_reject(self):
        """Promise constructor can reject via executor_fn."""
        from src.promise import Promise
        def executor(resolve, reject):
            reject(RuntimeError("failed"))
        p = Promise(executor)
        with pytest.raises(RuntimeError, match="failed"):
            p.result(timeout=2)


class TestPromiseThen:
    @pytest.mark.fail_to_pass
    def test_then_transforms_value(self):
        """then() should transform the resolved value."""
        from src.promise import Promise
        p = Promise.resolve(10).then(lambda v: v * 2)
        assert p.result(timeout=2) == 20

    @pytest.mark.fail_to_pass
    def test_then_chaining(self):
        """Multiple .then() calls chain transformations."""
        from src.promise import Promise
        p = Promise.resolve(1).then(lambda v: v + 1).then(lambda v: v * 3)
        assert p.result(timeout=2) == 6

    @pytest.mark.fail_to_pass
    def test_then_skipped_on_rejection(self):
        """If promise is rejected, then(on_fulfilled) is skipped."""
        from src.promise import Promise
        p = Promise.reject(ValueError("err")).then(lambda v: v * 2)
        with pytest.raises(ValueError, match="err"):
            p.result(timeout=2)


class TestPromiseCatch:
    @pytest.mark.fail_to_pass
    def test_catch_handles_rejection(self):
        """catch() should handle rejected promise and recover."""
        from src.promise import Promise
        p = Promise.reject(ValueError("err")).catch(lambda e: "recovered")
        assert p.result(timeout=2) == "recovered"

    @pytest.mark.fail_to_pass
    def test_catch_not_called_on_resolve(self):
        """catch() is skipped for resolved promises."""
        from src.promise import Promise
        p = Promise.resolve(42).catch(lambda e: "caught")
        assert p.result(timeout=2) == 42

    @pytest.mark.fail_to_pass
    def test_error_propagation_through_chain(self):
        """Errors propagate through .then() until .catch()."""
        from src.promise import Promise
        p = (Promise.reject(ValueError("original"))
             .then(lambda v: v * 2)
             .then(lambda v: v + 1)
             .catch(lambda e: f"caught: {e}"))
        assert p.result(timeout=2) == "caught: original"


class TestPromiseFinally:
    @pytest.mark.fail_to_pass
    def test_finally_called_on_resolve(self):
        """finally_() runs on resolution."""
        from src.promise import Promise
        side_effects = []
        p = Promise.resolve(42).finally_(lambda: side_effects.append("cleaned"))
        result = p.result(timeout=2)
        assert result == 42
        assert side_effects == ["cleaned"]

    @pytest.mark.fail_to_pass
    def test_finally_called_on_reject(self):
        """finally_() runs on rejection and preserves the rejection."""
        from src.promise import Promise
        side_effects = []
        p = Promise.reject(ValueError("err")).finally_(lambda: side_effects.append("cleaned"))
        with pytest.raises(ValueError, match="err"):
            p.result(timeout=2)
        assert side_effects == ["cleaned"]


class TestPromiseAll:
    @pytest.mark.fail_to_pass
    def test_all_resolves(self):
        """Promise.all resolves with list of values when all resolve."""
        from src.promise import Promise
        p1 = Promise.resolve(1)
        p2 = Promise.resolve(2)
        p3 = Promise.resolve(3)
        p = Promise.all([p1, p2, p3])
        assert p.result(timeout=2) == [1, 2, 3]

    @pytest.mark.fail_to_pass
    def test_all_rejects_on_first_failure(self):
        """Promise.all rejects if any input promise rejects."""
        from src.promise import Promise
        p1 = Promise.resolve(1)
        p2 = Promise.reject(ValueError("fail"))
        p3 = Promise.resolve(3)
        p = Promise.all([p1, p2, p3])
        with pytest.raises(ValueError, match="fail"):
            p.result(timeout=2)


class TestPromiseRace:
    @pytest.mark.fail_to_pass
    def test_race_resolves_with_first(self):
        """Promise.race resolves with the first settled promise."""
        from src.promise import Promise

        def slow(resolve, reject):
            import time
            time.sleep(0.5)
            resolve("slow")

        fast = Promise.resolve("fast")
        slow_p = Promise(slow)
        p = Promise.race([slow_p, fast])
        assert p.result(timeout=2) == "fast"

    @pytest.mark.fail_to_pass
    def test_race_rejects_with_first_rejection(self):
        """Promise.race rejects if the first settled promise rejects."""
        from src.promise import Promise

        def slow(resolve, reject):
            import time
            time.sleep(0.5)
            resolve("slow")

        fast_reject = Promise.reject(ValueError("fast fail"))
        slow_p = Promise(slow)
        p = Promise.race([slow_p, fast_reject])
        with pytest.raises(ValueError, match="fast fail"):
            p.result(timeout=2)
