"""
PII Redaction and Sensitive Data Scrubbing Engine.
Sanitizes personal identifiable information (emails, phone numbers, SSNs, credit cards, raw medical notes)
before data is passed to logging sinks, persistent database storage, or telemetry spans.
"""

import re
from typing import Any, Dict, List, Union


class PIIRedactor:
    """
    Regex and schema-based PII Redactor for redacting sensitive user information
    and sanitizing logs, database entries, and telemetry span attributes.
    """

    # Common Regex Patterns for PII Detection
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_REGEX = re.compile(r'\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b')
    SSN_REGEX = re.compile(r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b')
    CREDIT_CARD_REGEX = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b')

    # Fields that should be masked or sanitized in dictionary payloads
    SENSITIVE_FIELD_NAMES = {
        "email", "phone", "ssn", "credit_card", "card_number",
        "password", "secret", "medical_history", "raw_medical_notes"
    }

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts PII patterns from plain text or prompt strings."""
        if not isinstance(text, str):
            return text

        redacted = text
        redacted = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", redacted)
        redacted = cls.PHONE_REGEX.sub("[REDACTED_PHONE]", redacted)
        redacted = cls.SSN_REGEX.sub("[REDACTED_SSN]", redacted)
        redacted = cls.CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", redacted)
        return redacted

    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redacts dictionary keys and values."""
        if not isinstance(data, dict):
            return data

        redacted_dict = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in cls.SENSITIVE_FIELD_NAMES:
                redacted_dict[key] = "[REDACTED_SENSITIVE_FIELD]"
            elif isinstance(value, str):
                redacted_dict[key] = cls.redact_text(value)
            elif isinstance(value, dict):
                redacted_dict[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                redacted_dict[key] = cls.redact_list(value)
            else:
                redacted_dict[key] = value

        return redacted_dict

    @classmethod
    def redact_list(cls, data_list: List[Any]) -> List[Any]:
        """Recursively redacts elements in a list."""
        if not isinstance(data_list, list):
            return data_list

        redacted_items = []
        for item in data_list:
            if isinstance(item, str):
                redacted_items.append(cls.redact_text(item))
            elif isinstance(item, dict):
                redacted_items.append(cls.redact_dict(item))
            elif isinstance(item, list):
                redacted_items.append(cls.redact_list(item))
            else:
                redacted_items.append(item)

        return redacted_items

    @classmethod
    def redact_any(cls, value: Any) -> Any:
        """Universal redactor dispatcher for string, dict, list, or primitive types."""
        if isinstance(value, str):
            return cls.redact_text(value)
        elif isinstance(value, dict):
            return cls.redact_dict(value)
        elif isinstance(value, list):
            return cls.redact_list(value)
        return value
