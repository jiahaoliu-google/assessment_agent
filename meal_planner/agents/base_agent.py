"""
Base Agent Abstract Class for Multi-Agent System with MCP & Tool Calling Integration.
Integrated with OpenTelemetry tracing spans, Structured JSON Logging, and PII Scrubbing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from meal_planner.llm.router import StrategicModelRouter
from meal_planner.llm.provider import LLMResponse
from meal_planner.models import AgentMessage, MemoryNode
from meal_planner.tools.registry import ToolRegistry
from meal_planner.tools.base import ToolResult
from meal_planner.telemetry.redactor import PIIRedactor
from meal_planner.telemetry.logging import default_json_logger
from meal_planner.telemetry.tracing import default_tracer
from meal_planner.utils.ui import log_agent_action, CYAN, RED, GREEN


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents in the meal planning system.
    Supports system prompts, strategic LLM model routing, inter-agent messaging,
    persistent session memory, OpenTelemetry tracing spans, and JSON logging.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str = "",
        tool_registry: Optional[ToolRegistry] = None,
        session_id: Optional[str] = None,
        model_router: Optional[StrategicModelRouter] = None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt.strip()
        self.tool_registry = tool_registry if tool_registry else ToolRegistry()
        self.session_id = session_id
        self.model_router = model_router if model_router else StrategicModelRouter()
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        self.local_memories: List[MemoryNode] = []

    def execute_llm_generation(self, prompt: str, json_schema: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """Executes strategic LLM routing and generation under an OpenTelemetry span."""
        span = default_tracer.start_span(
            name=f"{self.name}.llm_generation",
            attributes={"agent.name": self.name, "session_id": self.session_id}
        )
        tier = self.model_router.get_tier_for_agent(self.name)
        sanitized_prompt = PIIRedactor.redact_text(prompt)

        self.log(f"🧠 Dispatching task to LLM Router (Tier: '{tier.value}')", color=CYAN)
        response = self.model_router.route_and_generate(
            agent_name=self.name,
            prompt=sanitized_prompt,
            system_prompt=self.system_prompt,
            json_schema=json_schema
        )
        default_tracer.end_span(span)
        return response

    def receive_message(self, message: AgentMessage):
        """Adds incoming message to agent inbox with PII redaction."""
        sanitized_payload = PIIRedactor.redact_dict(message.payload)
        sanitized_msg = AgentMessage(
            sender=message.sender,
            recipient=message.recipient,
            message_type=message.message_type,
            payload=sanitized_payload,
            timestamp=message.timestamp
        )
        self.inbox.append(sanitized_msg)

    def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]) -> AgentMessage:
        """Constructs an AgentMessage and stores it in outbox with PII redaction."""
        sanitized_payload = PIIRedactor.redact_dict(payload)
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            payload=sanitized_payload
        )
        self.outbox.append(msg)
        return msg

    def build_agent_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs a complete LLM operational context prompt payload combining:
        1. System Prompt & Agent Role
        2. Inbox Messages History
        3. Local & Session Memories
        4. Runtime Input Arguments
        """
        return PIIRedactor.redact_dict({
            "system_prompt": self.system_prompt,
            "agent_name": self.name,
            "agent_role": self.role,
            "session_id": self.session_id,
            "inbox_messages": [m.payload for m in self.inbox],
            "memories": [m.value for m in self.local_memories],
            "input_data": input_data
        })

    def invoke_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Invokes an LLM tool through the ToolRegistry/MCP server under an OpenTelemetry span.
        """
        span = default_tracer.start_span(
            name=f"{self.name}.tool_call.{tool_name}",
            attributes={"tool.name": tool_name, "agent.name": self.name, "session_id": self.session_id}
        )
        sanitized_kwargs = PIIRedactor.redact_dict(kwargs)
        self.log(f"🛠️ Calling Tool: '{tool_name}' with args={sanitized_kwargs}", color=CYAN)

        result = self.tool_registry.execute_tool(tool_name, sanitized_kwargs)

        if result.success:
            self.log(f"  └─ Tool '{tool_name}' succeeded in {result.execution_time_ms:.1f}ms", color=GREEN)
            default_tracer.end_span(span, status="OK")
        else:
            self.log(f"  └─ ❌ Tool '{tool_name}' failed: {result.error_message}", color=RED)
            default_tracer.end_span(span, status="ERROR")

        return result

    def log(self, text: str, color: str = CYAN, payload: Optional[Dict[str, Any]] = None):
        """Logs action to terminal UI and emits structured JSON log."""
        sanitized_text = PIIRedactor.redact_text(text)
        log_agent_action(self.name, sanitized_text, color=color)

        trace_ctx = default_tracer.get_active_context()
        default_json_logger.info(
            message=sanitized_text,
            agent_name=self.name,
            session_id=self.session_id,
            trace_id=trace_ctx.get("trace_id"),
            span_id=trace_ctx.get("span_id"),
            payload=payload
        )

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method to be overridden by concrete agent implementation."""
        pass
