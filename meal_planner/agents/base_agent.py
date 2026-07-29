"""
Base Agent Abstract Class for Multi-Agent System.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from meal_planner.models import AgentMessage
from meal_planner.utils.ui import log_agent_action, CYAN


class BaseAgent(ABC):
    """Abstract base class for all specialized agents in the meal planning system."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
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

    def log(self, text: str, color: str = CYAN):
        """Logs action to terminal using UI utility."""
        log_agent_action(self.name, text, color=color)

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method to be overridden by concrete agent implementation."""
        pass
