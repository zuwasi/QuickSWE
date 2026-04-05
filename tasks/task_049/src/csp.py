"""
CSP (Communicating Sequential Processes) channel implementation.

Provides buffered and unbuffered channels with send/recv operations,
and a select() operation for multiplexing across multiple channels.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import deque
import threading
import time


class ChannelClosed(Exception):
    """Raised when operating on a closed channel."""
    pass


class Channel:
    """
    A CSP-style channel for inter-process communication.
    
    Supports buffered (capacity > 0) and unbuffered (capacity = 0) modes.
    """

    def __init__(self, name: str = "", capacity: int = 0):
        self.name = name
        self.capacity = capacity
        self._buffer: deque = deque()
        self._closed = False
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._send_waiters: List[Tuple[Any, threading.Event]] = []
        self._recv_waiters: List[threading.Event] = []
        self._recv_results: Dict[int, Any] = {}
        self.send_count = 0
        self.recv_count = 0

    def send(self, value: Any, timeout: Optional[float] = None) -> bool:
        """Send a value on the channel. Blocks if buffer is full."""
        with self._lock:
            if self._closed:
                raise ChannelClosed(f"Cannot send on closed channel '{self.name}'")

            if self.capacity > 0:
                if len(self._buffer) < self.capacity:
                    self._buffer.append(value)
                    self.send_count += 1
                    self._not_empty.notify()
                    return True
                # Buffer full — wait
                deadline = time.time() + timeout if timeout else None
                while len(self._buffer) >= self.capacity and not self._closed:
                    wait_time = (deadline - time.time()) if deadline else None
                    if wait_time is not None and wait_time <= 0:
                        return False
                    self._not_full.wait(timeout=wait_time)
                if self._closed:
                    raise ChannelClosed(f"Channel '{self.name}' closed while sending")
                self._buffer.append(value)
                self.send_count += 1
                self._not_empty.notify()
                return True
            else:
                # Unbuffered: rendezvous
                self._buffer.append(value)
                self.send_count += 1
                self._not_empty.notify()
                return True

    def recv(self, timeout: Optional[float] = None) -> Tuple[Any, bool]:
        """
        Receive a value from the channel.
        Returns (value, ok). ok is False if channel is closed and empty.
        """
        with self._lock:
            if self._buffer:
                value = self._buffer.popleft()
                self.recv_count += 1
                self._not_full.notify()
                return (value, True)

            if self._closed:
                return (None, False)

            deadline = time.time() + timeout if timeout else None
            while not self._buffer and not self._closed:
                wait_time = (deadline - time.time()) if deadline else None
                if wait_time is not None and wait_time <= 0:
                    return (None, False)
                self._not_empty.wait(timeout=wait_time)

            if self._buffer:
                value = self._buffer.popleft()
                self.recv_count += 1
                self._not_full.notify()
                return (value, True)

            return (None, False)

    def try_recv(self) -> Tuple[Any, bool]:
        """Non-blocking receive. Returns (value, ok)."""
        with self._lock:
            if self._buffer:
                value = self._buffer.popleft()
                self.recv_count += 1
                self._not_full.notify()
                return (value, True)
            return (None, False)

    def try_send(self, value: Any) -> bool:
        """Non-blocking send. Returns True if successful."""
        with self._lock:
            if self._closed:
                raise ChannelClosed(f"Cannot send on closed channel '{self.name}'")
            if self.capacity > 0 and len(self._buffer) < self.capacity:
                self._buffer.append(value)
                self.send_count += 1
                self._not_empty.notify()
                return True
            elif self.capacity == 0:
                self._buffer.append(value)
                self.send_count += 1
                self._not_empty.notify()
                return True
            return False

    def is_ready(self) -> bool:
        """Check if the channel has data ready to receive."""
        with self._lock:
            return len(self._buffer) > 0

    def close(self):
        """Close the channel."""
        with self._lock:
            self._closed = True
            self._not_empty.notify_all()
            self._not_full.notify_all()

    @property
    def is_closed(self) -> bool:
        return self._closed

    def __repr__(self):
        return f"Channel('{self.name}', cap={self.capacity}, buf={len(self._buffer)})"


@dataclass
class SelectCase:
    """A case in a select statement."""
    channel: Channel
    is_send: bool = False
    send_value: Any = None


@dataclass
class SelectResult:
    """Result of a select operation."""
    index: int
    channel: Channel
    value: Any = None
    ok: bool = True


def select(cases: List[SelectCase], timeout: Optional[float] = None) -> Optional[SelectResult]:
    """
    Select waits on multiple channel operations and performs the one that is ready.
    If multiple are ready, it should choose one at random for fairness.
    
    Returns SelectResult for the chosen case, or None on timeout.
    """
    deadline = time.time() + timeout if timeout is not None else None

    while True:
        # Check each case in order
        for i, case in enumerate(cases):
            if case.is_send:
                if not case.channel.is_closed:
                    with case.channel._lock:
                        if case.channel.capacity == 0 or len(case.channel._buffer) < case.channel.capacity:
                            case.channel._buffer.append(case.send_value)
                            case.channel.send_count += 1
                            case.channel._not_empty.notify()
                            return SelectResult(index=i, channel=case.channel, ok=True)
            else:
                value, ok = case.channel.try_recv()
                if ok:
                    return SelectResult(index=i, channel=case.channel, value=value, ok=True)
                if case.channel.is_closed:
                    return SelectResult(index=i, channel=case.channel, value=None, ok=False)

        if deadline is not None and time.time() >= deadline:
            return None

        time.sleep(0.001)


class Pipeline:
    """A pipeline of channels connecting processing stages."""

    def __init__(self):
        self.channels: List[Channel] = []
        self.stages: List[Any] = []

    def add_stage(self, name: str, capacity: int = 1) -> Channel:
        ch = Channel(name=name, capacity=capacity)
        self.channels.append(ch)
        return ch

    def close_all(self):
        for ch in self.channels:
            ch.close()


class FanOut:
    """Fan-out: send to multiple channels."""

    def __init__(self, channels: List[Channel]):
        self.channels = channels

    def send(self, value: Any):
        for ch in self.channels:
            ch.send(value)


class FanIn:
    """Fan-in: receive from any of multiple channels."""

    def __init__(self, channels: List[Channel]):
        self.channels = channels

    def recv(self, timeout: Optional[float] = None) -> Optional[SelectResult]:
        cases = [SelectCase(channel=ch) for ch in self.channels]
        return select(cases, timeout=timeout)
