"""
Model Context Protocol (MCP) Server Implementation.
Implements MCP JSON-RPC 2.0 specification for tools/list and tools/call endpoints.
"""

import json
from typing import Dict, Any, Optional
from meal_planner.tools.registry import ToolRegistry


class MCPServer:
    """
    Model Context Protocol (MCP) Server.
    Provides standard JSON-RPC 2.0 protocol interface for LLM client integration.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry if registry else ToolRegistry()
        self.server_name = "MealPlannerMCPServer"
        self.protocol_version = "2024-11-05"

    def handle_json_rpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main JSON-RPC 2.0 entry point.
        Handles 'initialize', 'tools/list', and 'tools/call'.
        """
        jsonrpc = request.get("jsonrpc", "2.0")
        req_id = request.get("id", 1)
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "protocolVersion": self.protocol_version,
                    "serverInfo": {
                        "name": self.server_name,
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {"listChanged": True}
                    }
                }
            }

        elif method == "tools/list":
            tools_list = []
            for t_schema in self.registry.list_tools():
                fn = t_schema["function"]
                tools_list.append({
                    "name": fn["name"],
                    "description": fn["description"],
                    "inputSchema": fn["parameters"]
                })
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "result": {
                    "tools": tools_list
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                return {
                    "jsonrpc": jsonrpc,
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: 'name' is required for tools/call."
                    }
                }

            result = self.registry.execute_tool(tool_name, arguments)

            if result.success:
                return {
                    "jsonrpc": jsonrpc,
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result.data, indent=2)
                            }
                        ],
                        "isError": False
                    }
                }
            else:
                return {
                    "jsonrpc": jsonrpc,
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Tool Execution Error: {result.error_message}"
                            }
                        ],
                        "isError": True
                    }
                }

        else:
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: '{method}'"
                }
            }
