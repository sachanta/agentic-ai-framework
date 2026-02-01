"""
Distributed tracing for agent operations.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import uuid


@dataclass
class Span:
    """A span representing a unit of work in a trace."""

    trace_id: str
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "running"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def end(self, status: str = "ok") -> None:
        """End the span."""
        self.end_time = datetime.utcnow()
        self.status = status

    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> None:
        """Add an event to the span."""
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.utcnow().isoformat(),
                "attributes": attributes or {},
            }
        )

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        self.attributes[key] = value


class Tracer:
    """
    Tracer for creating and managing spans.

    Provides distributed tracing capabilities for agent operations.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._spans: Dict[str, Span] = {}
        self._current_span: Optional[Span] = None

    def create_span(
        self,
        name: str,
        trace_id: str = None,
        parent_span_id: str = None,
        attributes: Dict[str, Any] = None,
    ) -> Span:
        """Create a new span."""
        span = Span(
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            name=name,
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )
        self._spans[span.span_id] = span
        return span

    @contextmanager
    def start_span(self, name: str, attributes: Dict[str, Any] = None):
        """Context manager for creating and managing a span."""
        parent_id = self._current_span.span_id if self._current_span else None
        trace_id = self._current_span.trace_id if self._current_span else None

        span = self.create_span(
            name=name,
            trace_id=trace_id,
            parent_span_id=parent_id,
            attributes=attributes,
        )

        previous_span = self._current_span
        self._current_span = span

        try:
            yield span
            span.end(status="ok")
        except Exception as e:
            span.set_attribute("error", str(e))
            span.end(status="error")
            raise
        finally:
            self._current_span = previous_span

    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return self._current_span

    def export_spans(self) -> List[Dict[str, Any]]:
        """Export all spans as dictionaries."""
        return [
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "name": span.name,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "status": span.status,
                "attributes": span.attributes,
                "events": span.events,
            }
            for span in self._spans.values()
        ]
