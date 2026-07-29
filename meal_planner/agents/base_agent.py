"""
Base Agent Abstract Class for Multi-Agent System with MCP & Tool Calling Integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from meal_planner.models import AgentMessage
from meal_planner.tools.registry import ToolRegistry
from meal_planner.tools.base import ToolResult
from meal_planner.utils.ui import log_agent_action, CYAN, RED, GREEN


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents in the meal planning system.
    Supports inter-agent messaging and explicit LLM tool calling via ToolRegistry & MCP.
    """

    def __init__(self, name: str, role: str, tool_registry: Optional[ToolRegistry] = None):
        self.name = name
        self.role = role
        self.tool_registry = tool_registry if tool_registry else ToolRegistry()
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []

    def receive_message(self, message: AgentMessage):
        """Adds incoming message to agent inbox."""
        self.inbox.append(message)

    def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]) -> AgentMessage:
        """Constructs an AgentMessage and stores it in outbox."""
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            payload=payload
        )
        self.outbox.append(msg)
        return msg

    def invoke_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Invokes an LLM tool through the ToolRegistry/MCP server with schema validation and error logging.
        """
        self.log(f"🛠️ Calling Tool: '{tool_name}' with args={kwargs}", color=CYAN)
        result = self.tool_registry.execute_tool(tool_name, kwargs)

        if result.success:
            self.log(f"  └─ Tool '{tool_name}' succeeded in {result.execution_time_ms:.1f}ms", color=GREEN)
        else:
            self.log(f"  └─ ❌ Tool '{tool_name}' failed: {result.error_message}", color=RED)

        return result

    def log(self, text: str, color: str = CYAN):
        """Logs action to terminal using UI utility."""
        log_agent_action(self.name, text, color=color)

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method to be overridden by concrete agent implementation."""
        pass
