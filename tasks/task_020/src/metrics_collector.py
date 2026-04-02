"""Metrics collector that observes data sources."""

import statistics
from .data_source import DataSource


class MetricsCollector:
    """Collects and aggregates metrics from one or more DataSource instances.

    Attaches itself as an observer to data sources. When data events
    arrive, it records them for later aggregation.
    """

    def __init__(self, collector_id: str):
        self.collector_id = collector_id
        self._values = {}       # source_id -> list of values
        self._sources = []      # list of DataSource references
        self._event_count = 0

    def observe(self, source: DataSource) -> None:
        """Start observing a data source.

        Attaches this collector's ``_on_event`` method to the source.
        """
        source.attach(self._on_event)
        self._sources.append(source)

    def stop_observing(self, source: DataSource) -> None:
        """Stop observing a specific data source."""
        source.detach(self._on_event)
        self._sources = [s for s in self._sources if s is not source]

    def stop_all(self) -> None:
        """Stop observing all data sources."""
        for source in self._sources:
            source.detach(self._on_event)
        self._sources.clear()

    def _on_event(self, event_type: str, data: dict) -> None:
        """Handle an event from a data source."""
        self._event_count += 1
        if event_type == "data":
            source_id = data.get("source_id", "unknown")
            value = data.get("value")
            if source_id not in self._values:
                self._values[source_id] = []
            self._values[source_id].append(value)

    def get_average(self, source_id: str) -> float:
        """Get the average value from a specific source."""
        values = self._values.get(source_id, [])
        if not values:
            return 0.0
        return statistics.mean(values)

    def get_count(self, source_id: str) -> int:
        """Get the count of data points from a specific source."""
        return len(self._values.get(source_id, []))

    def get_all_stats(self) -> dict:
        """Get statistics for all observed sources."""
        result = {}
        for source_id, values in self._values.items():
            if values:
                result[source_id] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                }
        return result

    @property
    def event_count(self):
        return self._event_count

    def __repr__(self):
        return f"MetricsCollector({self.collector_id!r})"
