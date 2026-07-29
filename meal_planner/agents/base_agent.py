"""
Base Agent Abstract Class for Multi-Agent System with MCP & Tool Calling Integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from meal_planner.models import AgentMessage, MemoryNode
from meal_planner.tools.registry import ToolRegistry
from meal_planner.tools.base import ToolResult
from meal_planner.utils.ui import log_agent_action, CYAN, RED, GREEN


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents in the meal planning system.
    Supports system prompts, inter-agent messaging, persistent session memory,
    and explicit LLM tool calling via ToolRegistry & MCP.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str = "",
        tool_registry: Optional[ToolRegistry] = None,
        session_id: Optional[str] = None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt.strip()
        self.tool_registry = tool_registry if tool_registry else ToolRegistry()
        self.session_id = session_id
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        self.local_memories: List[MemoryNode] = []

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

    def build_agent_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs a complete LLM operational context prompt payload combining:
        1. System Prompt & Agent Role
        2. Inbox Messages History
        3. Local & Session Memories
        4. Runtime Input Arguments
        """
        return {
            "system_prompt": self.system_prompt,
            "agent_name": self.name,
            "agent_role": self.role,
            "session_id": self.session_id,
            "inbox_messages": [m.payload for m in self.inbox],
            "memories": [m.value for m in self.local_memories],
            "input_data": input_data
        }

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

