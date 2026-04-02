"""Pipeline context for shared state between stages."""

import time
from collections import defaultdict


class PipelineContext:
    """Holds shared state accessible by all pipeline stages."""

    def __init__(self, config=None):
        self._state = {}
        self._metadata = {}
        self._timestamps = {}
        self._stage_results = {}
        self._error_log = []
        self._counters = defaultdict(int)
        self._config = config
        self._started_at = None
        self._finished_at = None

    def start(self):
        """Mark pipeline as started."""
        self._started_at = time.time()

    def finish(self):
        """Mark pipeline as finished."""
        self._finished_at = time.time()

    @property
    def elapsed(self):
        """Return elapsed time since start."""
        if self._started_at is None:
            return 0.0
        end = self._finished_at or time.time()
        return end - self._started_at

    def set(self, key, value):
        """Set a shared state value."""
        self._state[key] = value
        self._timestamps[key] = time.time()

    def get(self, key, default=None):
        """Get a shared state value."""
        return self._state.get(key, default)

    def has(self, key):
        """Check if a key exists in shared state."""
        return key in self._state

    def delete(self, key):
        """Remove a key from shared state."""
        if key in self._state:
            del self._state[key]
            if key in self._timestamps:
                del self._timestamps[key]

    def set_metadata(self, stage_name, key, value):
        """Set metadata for a specific stage."""
        if stage_name not in self._metadata:
            self._metadata[stage_name] = {}
        self._metadata[stage_name][key] = value

    def get_metadata(self, stage_name, key=None):
        """Get metadata for a specific stage."""
        stage_meta = self._metadata.get(stage_name, {})
        if key is None:
            return dict(stage_meta)
        return stage_meta.get(key)

    def record_stage_result(self, stage_name, items):
        """Record the output of a stage for inspection."""
        self._stage_results[stage_name] = items

    def get_stage_result(self, stage_name):
        """Get the recorded result of a specific stage."""
        return self._stage_results.get(stage_name)

    def increment(self, counter_name, amount=1):
        """Increment a named counter."""
        self._counters[counter_name] += amount

    def get_counter(self, counter_name):
        """Get a counter value."""
        return self._counters[counter_name]

    def log_error(self, stage_name, error, item=None):
        """Log an error that occurred during processing."""
        self._error_log.append({
            'stage': stage_name,
            'error': str(error),
            'error_type': type(error).__name__,
            'item': item,
            'timestamp': time.time()
        })

    def get_errors(self):
        """Return all logged errors."""
        return list(self._error_log)

    def has_errors(self):
        """Check if any errors have been logged."""
        return len(self._error_log) > 0

    def clear(self):
        """Reset all context state."""
        self._state.clear()
        self._metadata.clear()
        self._timestamps.clear()
        self._stage_results.clear()
        self._error_log.clear()
        self._counters.clear()
        self._started_at = None
        self._finished_at = None

    def summary(self):
        """Return a summary dict of the context."""
        return {
            'state_keys': list(self._state.keys()),
            'stages_completed': list(self._stage_results.keys()),
            'error_count': len(self._error_log),
            'counters': dict(self._counters),
            'elapsed': self.elapsed
        }
