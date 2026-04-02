import sys
import os
import gc
import weakref
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.observable import Observable
from src.data_source import DataSource
from src.metrics_collector import MetricsCollector


# ── pass-to-pass: basic observable and metrics functionality ──────


class TestObservableBasic:
    def test_attach_and_notify(self):
        obs = Observable()
        received = []
        obs.attach(lambda et, d: received.append((et, d)))
        obs.notify("test", {"x": 1})
        assert len(received) == 1
        assert received[0] == ("test", {"x": 1})

    def test_detach(self):
        obs = Observable()
        handler = lambda et, d: None
        obs.attach(handler)
        assert obs.observer_count == 1
        obs.detach(handler)
        assert obs.observer_count == 0

    def test_no_duplicate_attach(self):
        obs = Observable()
        handler = lambda et, d: None
        obs.attach(handler)
        obs.attach(handler)
        assert obs.observer_count == 1

    def test_notify_returns_count(self):
        obs = Observable()
        obs.attach(lambda et, d: None)
        obs.attach(lambda et, d: None)
        assert obs.notify("test") == 2

    def test_detach_nonexistent(self):
        obs = Observable()
        assert obs.detach(lambda et, d: None) is False


class TestDataSource:
    def test_emit_notifies(self):
        ds = DataSource("sensor_1")
        events = []
        ds.attach(lambda et, d: events.append(d))
        ds.emit(42.5)
        assert len(events) == 1
        assert events[0]["value"] == 42.5

    def test_emit_count(self):
        ds = DataSource("sensor_1")
        ds.emit(1)
        ds.emit(2)
        assert ds.emit_count == 2

    def test_last_value(self):
        ds = DataSource("sensor_1")
        ds.emit(99.9)
        assert ds.last_value == 99.9

    def test_emit_status(self):
        ds = DataSource("sensor_1")
        events = []
        ds.attach(lambda et, d: events.append((et, d)))
        ds.emit_status("healthy")
        assert events[0][0] == "status"
        assert events[0][1]["status"] == "healthy"


class TestMetricsCollector:
    def test_observe_and_collect(self):
        ds = DataSource("s1")
        mc = MetricsCollector("mc1")
        mc.observe(ds)
        ds.emit(10)
        ds.emit(20)
        ds.emit(30)
        assert mc.get_count("s1") == 3
        assert mc.get_average("s1") == 20.0

    def test_multiple_sources(self):
        ds1 = DataSource("s1")
        ds2 = DataSource("s2")
        mc = MetricsCollector("mc1")
        mc.observe(ds1)
        mc.observe(ds2)
        ds1.emit(10)
        ds2.emit(100)
        assert mc.get_count("s1") == 1
        assert mc.get_count("s2") == 1

    def test_stop_observing(self):
        ds = DataSource("s1")
        mc = MetricsCollector("mc1")
        mc.observe(ds)
        mc.stop_observing(ds)
        ds.emit(10)
        assert mc.get_count("s1") == 0

    def test_stop_all(self):
        ds1 = DataSource("s1")
        ds2 = DataSource("s2")
        mc = MetricsCollector("mc1")
        mc.observe(ds1)
        mc.observe(ds2)
        mc.stop_all()
        ds1.emit(10)
        ds2.emit(20)
        assert mc.event_count == 0

    def test_get_all_stats(self):
        ds = DataSource("s1")
        mc = MetricsCollector("mc1")
        mc.observe(ds)
        ds.emit(10)
        ds.emit(20)
        stats = mc.get_all_stats()
        assert "s1" in stats
        assert stats["s1"]["count"] == 2
        assert stats["s1"]["mean"] == 15.0

    def test_average_empty(self):
        mc = MetricsCollector("mc1")
        assert mc.get_average("nonexistent") == 0.0


# ── fail-to-pass: memory leak when collectors are deleted ─────────


class TestMemoryLeak:
    @pytest.mark.fail_to_pass
    def test_deleted_collector_observer_count_drops(self):
        """When a MetricsCollector is deleted, the DataSource should
        no longer hold a reference to it, and observer_count should drop."""
        ds = DataSource("s1")
        mc = MetricsCollector("mc1")
        mc.observe(ds)
        assert ds.observer_count == 1

        # Delete the collector without explicit stop_observing
        del mc
        gc.collect()

        # After GC, the dead observer should be cleaned up
        # (either during notify or proactively)
        ds.emit(1)  # trigger cleanup if lazy
        assert ds.observer_count == 0, (
            f"Expected 0 observers after collector deletion, "
            f"got {ds.observer_count}"
        )

    @pytest.mark.fail_to_pass
    def test_collector_garbage_collected(self):
        """Deleted collectors should be garbage collected — the DataSource
        should not prevent GC by holding strong references."""
        ds = DataSource("s1")
        mc = MetricsCollector("mc1")
        weak_mc = weakref.ref(mc)
        mc.observe(ds)

        del mc
        gc.collect()

        assert weak_mc() is None, (
            "MetricsCollector was not garbage collected — "
            "DataSource is holding a strong reference"
        )

    @pytest.mark.fail_to_pass
    def test_many_collectors_no_leak(self):
        """Creating and deleting many collectors should not leak observers."""
        ds = DataSource("s1")

        for i in range(100):
            mc = MetricsCollector(f"mc_{i}")
            mc.observe(ds)
            del mc

        gc.collect()
        ds.emit(1)  # trigger cleanup

        assert ds.observer_count == 0, (
            f"Expected 0 observers after creating/deleting 100 collectors, "
            f"got {ds.observer_count}"
        )

    @pytest.mark.fail_to_pass
    def test_live_collectors_still_work_after_dead_cleanup(self):
        """Live collectors should continue to receive events even after
        dead collectors are cleaned up."""
        ds = DataSource("s1")

        # Create a collector that will be deleted
        dead_mc = MetricsCollector("dead")
        dead_mc.observe(ds)

        # Create a collector that stays alive
        live_mc = MetricsCollector("live")
        live_mc.observe(ds)

        # Delete the first one
        del dead_mc
        gc.collect()

        # Emit — should notify live_mc and clean up dead one
        ds.emit(42)

        assert live_mc.get_count("s1") == 1, "Live collector should still work"
        assert ds.observer_count == 1, (
            f"Should have 1 observer (live), got {ds.observer_count}"
        )
