"""
Multi-Agent Orchestrator Engine (MealPlannerOrchestrator).
Manages workflow state, agent handoffs, inter-agent messaging, ToolRegistry, MCP Server,
strategic LLM model routing, interactive Human-In-The-Loop (HITL) audit guardrails,
persistent SQLite session database, async memory operations, and context window history compaction.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from meal_planner.agents.profile_analyzer import ProfileAnalyzerAgent
from meal_planner.agents.nutritionist import NutritionistAgent
from meal_planner.agents.chef_planner import ChefMealPlannerAgent
from meal_planner.agents.dietary_auditor import DietaryAuditorAgent
from meal_planner.agents.grocery_prep import GroceryPrepAgent
from meal_planner.tools.registry import ToolRegistry
from meal_planner.tools.mcp_server import MCPServer
from meal_planner.utils.database import DatabaseManager
from meal_planner.memory.manager import AsyncMemoryManager
from meal_planner.llm.router import StrategicModelRouter
from meal_planner.hitl.manager import HITLManager, HITLDecision
from meal_planner.models import AgentMessage, SessionContext

from meal_planner.utils.ui import (
    print_banner, print_agent_header, print_box, print_table,
    CYAN, GREEN, YELLOW, MAGENTA, BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_MAGENTA, BOLD, RESET
)


class MealPlannerOrchestrator:
    """
    Orchestrates 5 specialized agents to create a complete 7-day meal plan with session,
    memory, strategic model routing, interactive HITL guardrails, and database persistence.
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        db_manager: Optional[DatabaseManager] = None,
        session_id: Optional[str] = None,
        model_router: Optional[StrategicModelRouter] = None,
        hitl_manager: Optional[HITLManager] = None,
        interactive_hitl: bool = False
    ):
        self.tool_registry = tool_registry if tool_registry else ToolRegistry()
        self.mcp_server = MCPServer(registry=self.tool_registry)
        self.db_manager = db_manager if db_manager else DatabaseManager()
        self.memory_manager = AsyncMemoryManager(db_manager=self.db_manager)
        self.model_router = model_router if model_router else StrategicModelRouter()
        self.hitl_manager = hitl_manager if hitl_manager else HITLManager(interactive=interactive_hitl)

        self.session_id = session_id if session_id else f"session_{uuid.uuid4().hex[:8]}"
        self.db_manager.save_session(self.session_id)

        self.profile_agent = ProfileAnalyzerAgent(tool_registry=self.tool_registry, session_id=self.session_id, model_router=self.model_router)
        self.nutritionist_agent = NutritionistAgent(tool_registry=self.tool_registry, session_id=self.session_id, model_router=self.model_router)
        self.chef_agent = ChefMealPlannerAgent(tool_registry=self.tool_registry, session_id=self.session_id, model_router=self.model_router)
        self.auditor_agent = DietaryAuditorAgent(tool_registry=self.tool_registry, session_id=self.session_id, model_router=self.model_router)
        self.grocery_agent = GroceryPrepAgent(tool_registry=self.tool_registry, session_id=self.session_id, model_router=self.model_router)

        self.session_messages: List[AgentMessage] = []

    def _run_async(self, coro):
        """Helper to run coroutines safely in synchronous or active loop contexts."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return loop.create_task(coro)
        else:
            return asyncio.run(coro)

    def _record_and_compact_messages(self, new_messages: List[AgentMessage]):
        """Records new messages to persistent DB and triggers async history compaction if history grows."""
        for msg in new_messages:
            self.session_messages.append(msg)
            self.db_manager.add_interaction_message(self.session_id, msg)

        # Trigger async history compaction
        compacted_res = self._run_async(
            self.memory_manager.compact_history_async(self.session_id, self.session_messages, max_messages=8)
        )
        if isinstance(compacted_res, list):
            self.session_messages = compacted_res

    def run(self, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the multi-agent pipeline with persistent memory context,
        strategic LLM model routing, and interactive HITL audit checkpoints.
        """
        print_banner()
        current_inputs = dict(user_inputs)

        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Step 1: User Profile & Goal Analyzer Agent
            print_agent_header(self.profile_agent.name, self.profile_agent.role, color=BRIGHT_CYAN)
            res1 = self.profile_agent.process(current_inputs)
            user_profile = res1["user_profile"]
            self.db_manager.save_user_profile(self.session_id, user_profile)
            self._record_and_compact_messages(self.profile_agent.outbox)

            # Step 2: Nutritionist Agent
            print_agent_header(self.nutritionist_agent.name, self.nutritionist_agent.role, color=BRIGHT_YELLOW)
            res2 = self.nutritionist_agent.process({"user_profile": user_profile})
            nutrition_target = res2["nutrition_target"]
            self._record_and_compact_messages(self.nutritionist_agent.outbox)

            # Step 3: Chef Meal Planner Agent
            print_agent_header(self.chef_agent.name, self.chef_agent.role, color=BRIGHT_MAGENTA)
            res3 = self.chef_agent.process({
                "user_profile": user_profile,
                "nutrition_target": nutrition_target
            })
            full_meal_plan = res3["full_meal_plan"]
            self._record_and_compact_messages(self.chef_agent.outbox)

            # Step 4: Quality Control Auditor Agent
            print_agent_header(self.auditor_agent.name, self.auditor_agent.role, color=BRIGHT_CYAN)
            res4 = self.auditor_agent.process({"full_meal_plan": full_meal_plan})
            audit_result = res4["audit_result"]
            self._record_and_compact_messages(self.auditor_agent.outbox)

            # --- Human-In-The-Loop (HITL) Guardrail Checkpoint ---
            hitl_decision: HITLDecision = self.hitl_manager.evaluate_audit_checkpoint(
                audit_result=audit_result,
                user_profile=user_profile,
                full_meal_plan=full_meal_plan
            )

            if hitl_decision.action == "refine_constraints" and hitl_decision.updated_inputs:
                current_inputs.update(hitl_decision.updated_inputs)
                continue  # Loop back with refined constraints
            elif hitl_decision.action == "abort":
                return {
                    "session_id": self.session_id,
                    "status": "aborted",
                    "user_profile": user_profile,
                    "nutrition_target": nutrition_target,
                    "full_meal_plan": full_meal_plan,
                    "audit_result": audit_result
                }
            else:
                break  # Proceed to Step 5

        # Step 5: Shopping List & Prep Specialist Agent
        print_agent_header(self.grocery_agent.name, self.grocery_agent.role, color=BRIGHT_GREEN)
        res5 = self.grocery_agent.process({"full_meal_plan": full_meal_plan})
        grocery_list = res5["grocery_list"]

        # Persist memory node summary
        self._run_async(
            self.memory_manager.store_memory(
                session_id=self.session_id,
                agent_name="MealPlannerOrchestrator",
                key="pipeline_completion",
                value={
                    "goal_type": user_profile.parsed_goal_type,
                    "target_calories": nutrition_target.target_calories,
                    "audit_score": audit_result.score
                },
                memory_type="long_term"
            )
        )

        return {
            "session_id": self.session_id,
            "status": "completed",
            "user_profile": user_profile,
            "nutrition_target": nutrition_target,
            "full_meal_plan": full_meal_plan,
            "audit_result": audit_result,
            "grocery_list": grocery_list
        }
