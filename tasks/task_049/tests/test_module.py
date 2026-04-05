import os
import sys
import pytest
import collections

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.csp import Channel, SelectCase, SelectResult, select, FanIn


class TestBasicChannel:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_buffered_send_recv(self):
        ch = Channel("test", capacity=3)
        ch.send(1)
        ch.send(2)
        val, ok = ch.recv()
        assert ok and val == 1
        val, ok = ch.recv()
        assert ok and val == 2

    @pytest.mark.pass_to_pass
    def test_try_recv_empty(self):
        ch = Channel("test", capacity=1)
        val, ok = ch.try_recv()
        assert not ok

    @pytest.mark.pass_to_pass
    def test_select_single_ready(self):
        ch = Channel("ch1", capacity=3)
        ch.send(42)
        cases = [SelectCase(channel=ch)]
        result = select(cases, timeout=1.0)
        assert result is not None
        assert result.value == 42


class TestSelectFairness:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_select_distributes_across_channels(self):
        """select should not always pick the first ready channel."""
        ch1 = Channel("ch1", capacity=100)
        ch2 = Channel("ch2", capacity=100)
        ch3 = Channel("ch3", capacity=100)

        for i in range(100):
            ch1.send(f"ch1_{i}")
            ch2.send(f"ch2_{i}")
            ch3.send(f"ch3_{i}")

        counts = collections.Counter()
        for _ in range(90):
            cases = [
                SelectCase(channel=ch1),
                SelectCase(channel=ch2),
                SelectCase(channel=ch3),
            ]
            result = select(cases, timeout=1.0)
            assert result is not None
            counts[result.index] += 1

        # With random selection over 90 tries, each channel should get at least a few
        assert counts[1] > 0, (
            f"Channel 2 was never selected. Distribution: {dict(counts)}"
        )
        assert counts[2] > 0, (
            f"Channel 3 was never selected. Distribution: {dict(counts)}"
        )

    @pytest.mark.fail_to_pass
    def test_select_not_deterministic(self):
        """Two runs of select with same setup should sometimes differ."""
        ch1 = Channel("ch1", capacity=50)
        ch2 = Channel("ch2", capacity=50)

        for i in range(50):
            ch1.send(i)
            ch2.send(i)

        first_choices = []
        for _ in range(20):
            cases = [SelectCase(channel=ch1), SelectCase(channel=ch2)]
            result = select(cases, timeout=1.0)
            assert result is not None
            first_choices.append(result.index)

        unique = set(first_choices)
        assert len(unique) > 1, (
            f"Select always chose index {first_choices[0]} — not random. "
            f"Choices: {first_choices}"
        )

    @pytest.mark.fail_to_pass
    def test_fan_in_fairness(self):
        """FanIn should receive from all channels, not just the first."""
        channels = [Channel(f"ch{i}", capacity=50) for i in range(4)]
        for ch in channels:
            for j in range(50):
                ch.send(f"{ch.name}_{j}")

        fan = FanIn(channels)
        counts = collections.Counter()
        for _ in range(40):
            result = fan.recv(timeout=1.0)
            assert result is not None
            counts[result.index] += 1

        # All channels should get some receives
        for i in range(4):
            assert counts[i] > 0, (
                f"Channel {i} never selected by FanIn. Distribution: {dict(counts)}"
            )
