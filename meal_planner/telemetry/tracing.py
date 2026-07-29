"""
OpenTelemetry (OTel) Distributed Tracing for Multi-Agent Workflows.
Manages trace context generation, span lifecycle, context propagation, and attribute annotation.
"""

import uuid
import time
import secrets
from typing import Dict, Any, Optional
from meal_planner.telemetry.redactor import PIIRedactor


class SpanContext:
    """Represents an active OpenTelemetry tracing span."""

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = secrets.token_hex(8)  # W3C 64-bit hex span ID
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.events: list = []
        self.status: str = "UNSET"

    def set_attribute(self, key: str, value: Any):
        """Sets a PII-redacted span attribute."""
        self.attributes[key] = PIIRedactor.redact_any(value)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Records an event in the active span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": PIIRedactor.redact_dict(attributes) if attributes else {}
        })

    def end(self, status: str = "OK"):
        """Closes the span."""
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return (end - self.start_time) * 1000.0


class AgentTracer:
    """
    OpenTelemetry Tracer for creating spans, propagating trace context across agents,
    and recording multi-agent handoffs, tool calls, and database transactions.
    """

    def __init__(self, service_name: str = "meal_planner_system"):
        self.service_name = service_name
        self.current_trace_id: str = secrets.token_hex(16)  # W3C 128-bit hex trace ID
        self.active_spans: list = []
        self.completed_spans: list = []

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Starts a new trace or adopts incoming trace ID context."""
        self.current_trace_id = trace_id if trace_id else secrets.token_hex(16)
        return self.current_trace_id

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> SpanContext:
        """Starts a child span under active trace context."""
        parent_id = self.active_spans[-1].span_id if self.active_spans else None
        span = SpanContext(name=name, trace_id=self.current_trace_id, parent_span_id=parent_id)

        span.set_attribute("service.name", self.service_name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)

        self.active_spans.append(span)
        return span

    def end_span(self, span: SpanContext, status: str = "OK"):
        """Closes specified span and pops from active stack."""
        span.end(status=status)
        if span in self.active_spans:
            self.active_spans.remove(span)
        self.completed_spans.append(span)

    def get_active_context(self) -> Dict[str, str]:
        """Returns W3C trace context header values for inter-agent propagation."""
        active_span = self.active_spans[-1] if self.active_spans else None
        return {
            "trace_id": self.current_trace_id,
            "span_id": active_span.span_id if active_span else "",
            "service_name": self.service_name
        }


# Global tracer instance
default_tracer = AgentTracer()
