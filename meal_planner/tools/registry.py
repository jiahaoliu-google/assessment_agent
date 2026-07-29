"""
ToolRegistry: Central manager for registering, discovering, and executing LLM tools and MCP servers.
"""

from typing import Dict, Any, List, Optional
from meal_planner.tools.base import Tool, ToolResult, ToolNotFoundError, ToolValidationError
from meal_planner.tools.builtin_tools import BUILTIN_TOOLS


class ToolRegistry:
    """
    Central repository for tools.
    Handles tool registration, discovery, parameter validation, and execution.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        # Register built-in tools by default
        for t in BUILTIN_TOOLS:
            self.register_tool(t)

    def register_tool(self, tool: Tool):
        """Registers a new tool into the registry."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        """Retrieves a registered tool by name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' is not registered in the ToolRegistry.")
        return self._tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists all registered tools formatted as standard LLM OpenAI/Gemini JSON schemas."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def list_tool_names(self) -> List[str]:
        """Returns names of all registered tools."""
        return list(self._tools.keys())

    def execute_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> ToolResult:
        """
        Executes a registered tool by name with arguments validation and error handling.
        """
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error_message=f"ToolNotFoundError: Tool '{tool_name}' not found. Available tools: {self.list_tool_names()}"
            )
        tool = self._tools[tool_name]
        return tool.execute(**kwargs)
