"""
Multi-Agent Orchestrator Engine (MealPlannerOrchestrator).
Manages workflow state, agent handoffs, inter-agent messaging, ToolRegistry, and MCP Server.
"""

from typing import Dict, Any, Optional
from meal_planner.agents.profile_analyzer import ProfileAnalyzerAgent
from meal_planner.agents.nutritionist import NutritionistAgent
from meal_planner.agents.chef_planner import ChefMealPlannerAgent
from meal_planner.agents.dietary_auditor import DietaryAuditorAgent
from meal_planner.agents.grocery_prep import GroceryPrepAgent
from meal_planner.tools.registry import ToolRegistry
from meal_planner.tools.mcp_server import MCPServer

from meal_planner.utils.ui import (
    print_banner, print_agent_header, print_box, print_table,
    CYAN, GREEN, YELLOW, MAGENTA, BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_MAGENTA, BOLD, RESET
)


class MealPlannerOrchestrator:
    """Orchestrates the 5 specialized agents to create a complete 7-day meal plan via ToolRegistry & MCP."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry if tool_registry else ToolRegistry()
        self.mcp_server = MCPServer(registry=self.tool_registry)

        self.profile_agent = ProfileAnalyzerAgent(tool_registry=self.tool_registry)
        self.nutritionist_agent = NutritionistAgent(tool_registry=self.tool_registry)
        self.chef_agent = ChefMealPlannerAgent(tool_registry=self.tool_registry)
        self.auditor_agent = DietaryAuditorAgent(tool_registry=self.tool_registry)
        self.grocery_agent = GroceryPrepAgent(tool_registry=self.tool_registry)

    def run(self, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the complete multi-agent pipeline sequentially with agent-to-agent message passing and LLM tool calls.
        """
        print_banner()

        # Step 1: User Profile & Goal Analyzer Agent
        print_agent_header(self.profile_agent.name, self.profile_agent.role, color=BRIGHT_CYAN)
        res1 = self.profile_agent.process(user_inputs)
        user_profile = res1["user_profile"]

        # Step 2: Nutritionist Agent
        print_agent_header(self.nutritionist_agent.name, self.nutritionist_agent.role, color=BRIGHT_YELLOW)
        res2 = self.nutritionist_agent.process({"user_profile": user_profile})
        nutrition_target = res2["nutrition_target"]

        # Step 3: Chef Meal Planner Agent
        print_agent_header(self.chef_agent.name, self.chef_agent.role, color=BRIGHT_MAGENTA)
        res3 = self.chef_agent.process({
            "user_profile": user_profile,
            "nutrition_target": nutrition_target
        })
        full_meal_plan = res3["full_meal_plan"]

        # Step 4: Quality Control Auditor Agent
        print_agent_header(self.auditor_agent.name, self.auditor_agent.role, color=BRIGHT_CYAN)
        res4 = self.auditor_agent.process({"full_meal_plan": full_meal_plan})
        audit_result = res4["audit_result"]

        # Step 5: Shopping List & Prep Specialist Agent
        print_agent_header(self.grocery_agent.name, self.grocery_agent.role, color=BRIGHT_GREEN)
        res5 = self.grocery_agent.process({"full_meal_plan": full_meal_plan})
        grocery_list = res5["grocery_list"]

        return {
            "user_profile": user_profile,
            "nutrition_target": nutrition_target,
            "full_meal_plan": full_meal_plan,
            "audit_result": audit_result,
            "grocery_list": grocery_list
        }
