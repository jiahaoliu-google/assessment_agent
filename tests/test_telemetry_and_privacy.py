"""
Unit tests for Structured JSON Logging, OpenTelemetry Distributed Tracing, and PII Redaction.
"""

import io
import json
import unittest
from meal_planner.telemetry.redactor import PIIRedactor
from meal_planner.telemetry.logging import StructuredJSONLogger
from meal_planner.telemetry.tracing import AgentTracer, SpanContext
from meal_planner.utils.database import DatabaseManager
from meal_planner.models import AgentMessage


class TestPIIRedactor(unittest.TestCase):

    def test_redact_email_phone_ssn_card(self):
        """Tests text redaction of emails, phone numbers, SSNs, and credit cards."""
        text = "Contact user john.doe@example.com or call (555) 019-2834. SSN is 123-45-6789 with card 4111111111111111."
        redacted = PIIRedactor.redact_text(text)
        self.assertNotIn("john.doe@example.com", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertNotIn("555", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)
        self.assertNotIn("123-45-6789", redacted)
        self.assertIn("[REDACTED_SSN]", redacted)

    def test_redact_sensitive_dict_fields(self):
        """Tests dictionary key-based sensitive field redaction."""
        data = {
            "user_name": "Alice",
            "email": "alice@hospital.org",
            "phone": "555-123-4567",
            "medical_history": "Patient has diabetes type 2",
            "goals": "Lose weight safely"
        }
        redacted = PIIRedactor.redact_dict(data)
        self.assertEqual(redacted["email"], "[REDACTED_SENSITIVE_FIELD]")
        self.assertEqual(redacted["phone"], "[REDACTED_SENSITIVE_FIELD]")
        self.assertEqual(redacted["medical_history"], "[REDACTED_SENSITIVE_FIELD]")
        self.assertEqual(redacted["user_name"], "Alice")


class TestStructuredJSONLogger(unittest.TestCase):

    def setUp(self):
        self.stream = io.StringIO()
        self.json_logger = StructuredJSONLogger("test_logger", stream=self.stream)

    def test_json_output_format(self):
        """Tests that logger emits valid JSON with expected telemetry attributes."""
        self.json_logger.info(
            message="User session initiated for john.smith@company.com",
            session_id="session_test123",
            agent_name="TestAgent",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            payload={"action": "test_step"}
        )

        output = self.stream.getvalue().strip()
        parsed = json.loads(output)

        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["session_id"], "session_test123")
        self.assertEqual(parsed["agent_name"], "TestAgent")
        self.assertEqual(parsed["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertIn("[REDACTED_EMAIL]", parsed["message"])


class TestAgentTracer(unittest.TestCase):

    def setUp(self):
        self.tracer = AgentTracer(service_name="test_service")

    def test_span_lifecycle_and_parent_stack(self):
        """Tests OpenTelemetry span generation, parent-child context hierarchy, and duration."""
        trace_id = self.tracer.start_trace()
        self.assertEqual(len(trace_id), 32)  # 128-bit W3C hex string

        parent_span = self.tracer.start_span("orchestrator_run", {"step": "1"})
        child_span = self.tracer.start_span("agent_process", {"agent": "ProfileAnalyzer"})

        self.assertEqual(child_span.parent_span_id, parent_span.span_id)
        self.assertEqual(child_span.trace_id, trace_id)

        self.tracer.end_span(child_span)
        self.tracer.end_span(parent_span)

        self.assertEqual(len(self.tracer.completed_spans), 2)
        self.assertGreater(child_span.duration_ms, 0.0)


class TestDatabasePIIRedaction(unittest.TestCase):

    def test_database_stores_redacted_messages(self):
        """Tests that DatabaseManager automatically redacts PII before saving messages."""
        db = DatabaseManager(":memory:")
        session_id = "test_redact_session"
        db.save_session(session_id)

        msg = AgentMessage(
            sender="TestAgent",
            recipient="ReceiverAgent",
            message_type="TEST",
            payload={"contact": "Reach out to user@test.com at 555-888-9999"}
        )

        db.add_interaction_message(session_id, msg)
        history = db.get_interaction_history(session_id)

        self.assertEqual(len(history), 1)
        stored_payload = history[0].payload
        self.assertNotIn("user@test.com", stored_payload["contact"])
        self.assertIn("[REDACTED_EMAIL]", stored_payload["contact"])


if __name__ == "__main__":
    unittest.main()
