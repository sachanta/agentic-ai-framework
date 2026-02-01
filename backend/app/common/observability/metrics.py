"""
Metrics collection for monitoring agent performance.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from collections import defaultdict
import time


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collector for agent metrics.

    Provides counters, gauges, and histograms for monitoring.
    """

    def __init__(self, namespace: str = "agentic"):
        self.namespace = namespace
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._history: List[MetricPoint] = []

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Dict[str, str] = None,
    ) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] += value
        self._record(name, self._counters[key], labels)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None,
    ) -> None:
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._record(name, value, labels)

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None,
    ) -> None:
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        self._record(name, value, labels)

    def time_operation(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations."""

        class Timer:
            def __init__(timer_self):
                timer_self.start = None

            def __enter__(timer_self):
                timer_self.start = time.time()
                return timer_self

            def __exit__(timer_self, *args):
                duration = time.time() - timer_self.start
                self.observe_histogram(f"{name}_duration_seconds", duration, labels)

        return Timer()

    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get the current value of a counter."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get the current value of a gauge."""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get statistics for a histogram."""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def export_metrics(self) -> List[Dict[str, Any]]:
        """Export all metrics."""
        return [
            {
                "name": point.name,
                "value": point.value,
                "timestamp": point.timestamp.isoformat(),
                "labels": point.labels,
            }
            for point in self._history
        ]

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return f"{self.namespace}_{name}"
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{self.namespace}_{name}{{{label_str}}}"

    def _record(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record a metric point to history."""
        self._history.append(
            MetricPoint(
                name=f"{self.namespace}_{name}",
                value=value,
                labels=labels or {},
            )
        )
