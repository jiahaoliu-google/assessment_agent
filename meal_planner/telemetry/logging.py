"""
Structured JSON Logger with Automated PII Scrubbing.
Emits structured JSON log records containing timestamp, trace IDs, agent attributes, and sanitized payloads.
"""

import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from meal_planner.telemetry.redactor import PIIRedactor


class StructuredJSONFormatter(logging.Formatter):
    """Custom Logging Formatter that serializes LogRecord into PII-sanitized JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": PIIRedactor.redact_text(record.getMessage())
        }

        # Contextual metadata passed in extra
        session_id = getattr(record, "session_id", None)
        if session_id:
            log_entry["session_id"] = session_id

        agent_name = getattr(record, "agent_name", None)
        if agent_name:
            log_entry["agent_name"] = agent_name

        trace_id = getattr(record, "trace_id", None)
        if trace_id:
            log_entry["trace_id"] = trace_id

        span_id = getattr(record, "span_id", None)
        if span_id:
            log_entry["span_id"] = span_id

        extra_payload = getattr(record, "payload", None)
        if extra_payload:
            log_entry["payload"] = PIIRedactor.redact_any(extra_payload)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class StructuredJSONLogger:
    """Wrapper class providing clean structured JSON logging across agents and system components."""

    def __init__(self, name: str = "meal_planner", stream=None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = logging.StreamHandler(stream if stream else sys.stdout)
            handler.setFormatter(StructuredJSONFormatter())
            self.logger.addHandler(handler)

    def log(
        self,
        level: str,
        message: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ):
        extra = {
            "agent_name": agent_name,
            "session_id": session_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "payload": payload
        }
        level_upper = level.upper()
        if level_upper == "DEBUG":
            self.logger.debug(message, extra=extra)
        elif level_upper == "WARNING" or level_upper == "WARN":
            self.logger.warning(message, extra=extra)
        elif level_upper == "ERROR":
            self.logger.error(message, extra=extra)
        else:
            self.logger.info(message, extra=extra)

    def info(self, message: str, **kwargs):
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("ERROR", message, **kwargs)


# Global default logger instance
default_json_logger = StructuredJSONLogger("meal_planner_system")
