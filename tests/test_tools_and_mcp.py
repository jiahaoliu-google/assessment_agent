"""
Unit tests for ToolRegistry, LLM Tool JSON Schemas, MCP Server protocol, and Tool Error Handling.
"""

import unittest
import json
from meal_planner.tools.base import Tool, ToolValidationError, ToolNotFoundError, ToolResult
from meal_planner.tools.registry import ToolRegistry
from meal_planner.tools.mcp_server import MCPServer
from meal_planner.tools.builtin_tools import (
    tool_web_search_recipes,
    tool_fetch_ingredient_nutrition,
    tool_validate_dietary_restrictions,
    tool_calculate_tdee_and_macros
)


class TestToolsAndMCPServer(unittest.TestCase):

    def setUp(self):
        self.registry = ToolRegistry()
        self.mcp_server = MCPServer(registry=self.registry)

    def test_tool_docstring_and_schema_export(self):
        # Verify tool has description (docstring) and OpenAI JSON schema format
        schema = tool_calculate_tdee_and_macros.to_openai_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "calculate_tdee_and_macros")
        self.assertIn("description", schema["function"])
        self.assertIn("parameters", schema["function"])
        self.assertEqual(schema["function"]["parameters"]["type"], "object")

    def test_tool_parameter_schema_validation(self):
        # Missing required parameter test
        res = tool_calculate_tdee_and_macros.execute(
            height_cm=175.0,
            weight_kg=70.0
            # missing age, sex, activity_level, goal_type
        )
        self.assertFalse(res.success)
        self.assertIn("Validation Error", res.error_message)

        # Parameter type mismatch test
        res2 = tool_calculate_tdee_and_macros.execute(
            height_cm="invalid_string", # expected number
            weight_kg=70.0,
            age=25,
            sex="male",
            activity_level="moderate",
            goal_type="muscle_gain"
        )
        self.assertFalse(res2.success)
        self.assertIn("Validation Error", res2.error_message)

    def test_tool_execution_success(self):
        res = tool_calculate_tdee_and_macros.execute(
            height_cm=180.0,
            weight_kg=75.0,
            age=25,
            sex="male",
            activity_level="moderate",
            goal_type="muscle_gain"
        )
        self.assertTrue(res.success)
        self.assertIn("tdee_kcal", res.data)
        self.assertIn("target_calories_kcal", res.data)
        self.assertGreater(res.data["target_calories_kcal"], 2000)

    def test_validate_dietary_restrictions_tool(self):
        res = tool_validate_dietary_restrictions.execute(
            ingredients=["Chicken Breast", "Whole Milk", "Almonds"],
            exclusions=["dairy", "nuts"]
        )
        self.assertTrue(res.success)
        self.assertFalse(res.data["is_compliant"])
        self.assertEqual(res.data["total_violations"], 2)

    def test_mcp_server_initialize(self):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        resp = self.mcp_server.handle_json_rpc(req)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "MealPlannerMCPServer")

    def test_mcp_server_tools_list(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        resp = self.mcp_server.handle_json_rpc(req)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("web_search_recipes", tool_names)
        self.assertIn("calculate_tdee_and_macros", tool_names)
        self.assertIn("validate_dietary_restrictions", tool_names)

    def test_mcp_server_tools_call(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "web_search_recipes",
                "arguments": {
                    "query": "high protein keto breakfast",
                    "dietary_filter": "keto"
                }
            }
        }
        resp = self.mcp_server.handle_json_rpc(req)
        self.assertFalse(resp["result"]["isError"])
        content_text = resp["result"]["content"][0]["text"]
        parsed = json.loads(content_text)
        self.assertIn("results", parsed)


if __name__ == "__main__":
    unittest.main()
