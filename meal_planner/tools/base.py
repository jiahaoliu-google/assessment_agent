"""
Base classes, exceptions, and JSON schema validators for LLM Tool Calling and MCP integrations.
"""

import time
import json
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field


class ToolError(Exception):
    """Base exception for tool execution errors."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool arguments fail JSON schema validation."""
    pass


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found in the MCP server / registry."""
    pass


class ToolExecutionError(ToolError):
    """Raised when an error occurs during tool runtime execution."""
    pass


@dataclass
class ToolResult:
    """Structured result returned by tool execution."""
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message,
            "execution_time_ms": round(self.execution_time_ms, 2)
        }


class Tool:
    """
    Represents an LLM-compatible Tool with explicit name, docstring,
    JSON Schema parameters definition, and schema validation logic.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        handler: Callable[..., Any]
    ):
        self.name = name
        self.description = description.strip()
        self.parameters_schema = parameters_schema
        self.handler = handler

    def validate_arguments(self, kwargs: Dict[str, Any]) -> None:
        """
        Validates provided kwargs against the tool's parameters JSON Schema.
        Checks required fields and type primitive types.
        """
        schema_type = self.parameters_schema.get("type", "object")
        if schema_type == "object":
            properties = self.parameters_schema.get("properties", {})
            required = self.parameters_schema.get("required", [])

            # Check missing required fields
            missing = [r for r in required if r not in kwargs]
            if missing:
                raise ToolValidationError(
                    f"Tool '{self.name}' missing required parameters: {missing}. "
                    f"Expected schema: {json.dumps(self.parameters_schema)}"
                )

            # Check basic field types
            type_mapping = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict
            }

            for param, value in kwargs.items():
                if param in properties:
                    expected_type_str = properties[param].get("type")
                    if expected_type_str in type_mapping:
                        expected_type = type_mapping[expected_type_str]
                        # Python bool is subclass of int, prevent bool passing as integer/number
                        if expected_type_str in ["number", "integer"] and isinstance(value, bool):
                            raise ToolValidationError(
                                f"Tool '{self.name}' parameter '{param}' expected {expected_type_str}, got boolean {value}."
                            )
                        if not isinstance(value, expected_type):
                            raise ToolValidationError(
                                f"Tool '{self.name}' parameter '{param}' expected type '{expected_type_str}', got '{type(value).__name__}'."
                            )

    def execute(self, **kwargs) -> ToolResult:
        """
        Executes the tool with argument validation and error handling.
        Returns a structured ToolResult object.
        """
        start_time = time.time()
        try:
            # 1. Validate JSON schema
            self.validate_arguments(kwargs)

            # 2. Invoke handler
            data = self.handler(**kwargs)
            elapsed = (time.time() - start_time) * 1000.0

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                execution_time_ms=elapsed
            )

        except ToolValidationError as ve:
            elapsed = (time.time() - start_time) * 1000.0
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=f"Validation Error: {str(ve)}",
                execution_time_ms=elapsed
            )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000.0
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=f"Runtime Error during '{self.name}' execution: {str(e)}",
                execution_time_ms=elapsed
            )

    def to_openai_schema(self) -> Dict[str, Any]:
        """Formats tool declaration into standard LLM OpenAI/Gemini function specification."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
