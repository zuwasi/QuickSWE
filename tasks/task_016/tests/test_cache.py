import sys
import os
import time
import threading
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cache import ThreadSafeCache
from src.cache_manager import CacheManager
from src.cache_utils import make_cache_key, validate_ttl


# ── pass-to-pass: basic cache operations ──────────────────────────


class TestThreadSafeCacheBasic:
    def test_set_and_get(self):
        cache = ThreadSafeCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_returns_none(self):
        cache = ThreadSafeCache()
        assert cache.get("nonexistent") is None

    def test_delete(self):
        cache = ThreadSafeCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_missing(self):
        cache = ThreadSafeCache()
        assert cache.delete("nonexistent") is False

    def test_has(self):
        cache = ThreadSafeCache()
        cache.set("key1", "value1")
        assert cache.has("key1") is True
        assert cache.has("missing") is False

    def test_clear(self):
        cache = ThreadSafeCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size() == 0

    def test_size(self):
        cache = ThreadSafeCache()
        assert cache.size() == 0
        cache.set("a", 1)
        assert cache.size() == 1
        cache.set("b", 2)
        assert cache.size() == 2

    def test_eviction(self):
        cache = ThreadSafeCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # should evict "a"
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3


class TestCacheManagerBasic:
    def test_get_or_compute_caches_result(self):
        mgr = CacheManager()
        call_count = 0

        def compute():
            nonlocal call_count
            call_count += 1
            return 42

        result1 = mgr.get_or_compute("key1", compute)
        result2 = mgr.get_or_compute("key1", compute)
        assert result1 == 42
        assert result2 == 42
        assert call_count == 1

    def test_different_keys_compute_separately(self):
        mgr = CacheManager()
        r1 = mgr.get_or_compute("a", lambda: "alpha")
        r2 = mgr.get_or_compute("b", lambda: "beta")
        assert r1 == "alpha"
        assert r2 == "beta"

    def test_invalidate(self):
        mgr = CacheManager()
        mgr.get_or_compute("key1", lambda: "val1")
        mgr.invalidate("key1")
        call_count = 0

        def recompute():
            nonlocal call_count
            call_count += 1
            return "val2"

        result = mgr.get_or_compute("key1", recompute)
        assert result == "val2"
        assert call_count == 1

    def test_stats_tracking(self):
        mgr = CacheManager()
        mgr.get_or_compute("x", lambda: 1)
        mgr.get_or_compute("x", lambda: 2)
        stats = mgr.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["computations"] == 1

    def test_clear_resets_stats(self):
        mgr = CacheManager()
        mgr.get_or_compute("x", lambda: 1)
        mgr.clear()
        stats = mgr.get_stats()
        assert stats["hits"] == 0


class TestCacheUtils:
    def test_make_cache_key_deterministic(self):
        k1 = make_cache_key("foo", 42, bar="baz")
        k2 = make_cache_key("foo", 42, bar="baz")
        assert k1 == k2

    def test_make_cache_key_differs_for_different_args(self):
        k1 = make_cache_key("foo")
        k2 = make_cache_key("bar")
        assert k1 != k2

    def test_validate_ttl_none(self):
        assert validate_ttl(None) is None

    def test_validate_ttl_positive(self):
        assert validate_ttl(30) == 30.0

    def test_validate_ttl_negative_raises(self):
        with pytest.raises(ValueError):
            validate_ttl(-5)

    def test_validate_ttl_wrong_type_raises(self):
        with pytest.raises(TypeError):
            validate_ttl("ten")


# ── fail-to-pass: concurrent get_or_compute duplicate computation ──


class TestConcurrentComputation:
    @pytest.mark.fail_to_pass
    def test_concurrent_get_or_compute_single_computation(self):
        """Under concurrent access, compute_func must execute exactly once per key."""
        mgr = CacheManager()
        computation_count = 0
        count_lock = threading.Lock()
        barrier = threading.Barrier(20)

        def expensive_compute():
            nonlocal computation_count
            with count_lock:
                computation_count += 1
            time.sleep(0.05)  # simulate expensive work
            return "result"

        results = []
        errors = []

        def worker():
            try:
                barrier.wait(timeout=5)
                val = mgr.get_or_compute("shared_key", expensive_compute)
                results.append(val)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Worker threads raised errors: {errors}"
        assert all(r == "result" for r in results)
        # The critical assertion: computation should happen exactly once
        assert computation_count == 1, (
            f"Expected 1 computation, got {computation_count}"
        )

    @pytest.mark.fail_to_pass
    def test_concurrent_different_keys_all_compute(self):
        """Different keys should each compute exactly once even under concurrency."""
        mgr = CacheManager()
        computations = {}
        comp_lock = threading.Lock()
        barrier = threading.Barrier(10)

        def make_compute(k):
            def compute():
                with comp_lock:
                    computations[k] = computations.get(k, 0) + 1
                time.sleep(0.03)
                return f"value_{k}"
            return compute

        errors = []

        def worker(key):
            try:
                barrier.wait(timeout=5)
                mgr.get_or_compute(key, make_compute(key))
            except Exception as e:
                errors.append(e)

        # 2 threads per key, 5 keys = 10 threads
        threads = []
        for i in range(5):
            for _ in range(2):
                threads.append(threading.Thread(target=worker, args=(f"key_{i}",)))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors
        for i in range(5):
            assert computations.get(f"key_{i}", 0) == 1, (
                f"key_{i} computed {computations.get(f'key_{i}', 0)} times, expected 1"
            )

    @pytest.mark.fail_to_pass
    def test_stats_reflect_single_computation(self):
        """Stats should show 1 miss and 1 computation even with many concurrent requests."""
        mgr = CacheManager()
        barrier = threading.Barrier(10)

        def compute():
            time.sleep(0.03)
            return "value"

        def worker():
            barrier.wait(timeout=5)
            mgr.get_or_compute("stats_key", compute)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        stats = mgr.get_stats()
        assert stats["computations"] == 1, (
            f"Expected 1 computation in stats, got {stats['computations']}"
        )
