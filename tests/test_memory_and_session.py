"""
Unit tests for System Prompts, Persistent SQLite Database, Async Memory Manager,
History Compaction, and Session Context tracking.
"""

import unittest
import asyncio
import os
import tempfile
from meal_planner.models import UserProfile, AgentMessage, MemoryNode
from meal_planner.prompts.system_prompts import (
    PROFILE_ANALYZER_SYSTEM_PROMPT,
    NUTRITIONIST_SYSTEM_PROMPT,
    CHEF_PLANNER_SYSTEM_PROMPT,
    DIETARY_AUDITOR_SYSTEM_PROMPT,
    GROCERY_PREP_SYSTEM_PROMPT
)
from meal_planner.agents.profile_analyzer import ProfileAnalyzerAgent
from meal_planner.agents.nutritionist import NutritionistAgent
from meal_planner.agents.chef_planner import ChefMealPlannerAgent
from meal_planner.agents.dietary_auditor import DietaryAuditorAgent
from meal_planner.agents.grocery_prep import GroceryPrepAgent
from meal_planner.utils.database import DatabaseManager
from meal_planner.memory.manager import AsyncMemoryManager
from meal_planner.orchestrator import MealPlannerOrchestrator


class TestSystemPromptsDatabaseAndMemory(unittest.TestCase):

    def setUp(self):
        # Use an in-memory or temporary SQLite database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()

        self.db = DatabaseManager(db_path=self.temp_db_path)
        self.memory_manager = AsyncMemoryManager(db_manager=self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_system_prompts_presence_in_agents(self):
        """Verify each agent loads and retains its specific system prompt."""
        p_agent = ProfileAnalyzerAgent()
        n_agent = NutritionistAgent()
        c_agent = ChefMealPlannerAgent()
        a_agent = DietaryAuditorAgent()
        g_agent = GroceryPrepAgent()

        self.assertEqual(p_agent.system_prompt, PROFILE_ANALYZER_SYSTEM_PROMPT.strip())
        self.assertEqual(n_agent.system_prompt, NUTRITIONIST_SYSTEM_PROMPT.strip())
        self.assertEqual(c_agent.system_prompt, CHEF_PLANNER_SYSTEM_PROMPT.strip())
        self.assertEqual(a_agent.system_prompt, DIETARY_AUDITOR_SYSTEM_PROMPT.strip())
        self.assertEqual(g_agent.system_prompt, GROCERY_PREP_SYSTEM_PROMPT.strip())

        ctx = p_agent.build_agent_context({"test": 123})
        self.assertIn("system_prompt", ctx)
        self.assertEqual(ctx["agent_name"], "ProfileAnalyzerAgent")

    def test_parameterized_database_persistence(self):
        """Verify SQLite database CRUD operations using parameterized queries."""
        session_id = "test_sess_001"
        self.db.save_session(session_id, user_id="user_abc")

        profile = UserProfile(
            height_cm=182.0,
            weight_kg=78.0,
            raw_goal="Gain lean mass without dairy",
            parsed_goal_type="muscle_gain",
            caloric_target_offset=0.15,
            dietary_exclusions=["dairy"]
        )

        self.db.save_user_profile(session_id, profile)
        loaded_profile = self.db.get_user_profile(session_id)

        self.assertIsNotNone(loaded_profile)
        self.assertEqual(loaded_profile.height_cm, 182.0)
        self.assertEqual(loaded_profile.weight_kg, 78.0)
        self.assertIn("dairy", loaded_profile.dietary_exclusions)

        # Interaction message logging
        msg = AgentMessage(
            sender="TestSender",
            recipient="TestRecipient",
            message_type="TEST_MSG",
            payload={"status": "ok"}
        )
        self.db.add_interaction_message(session_id, msg)
        history = self.db.get_interaction_history(session_id)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].sender, "TestSender")
        self.assertEqual(history[0].payload["status"], "ok")

    def test_async_memory_operations(self):
        """Verify store, recall, and search memory functions using asyncio."""
        async def run_memory_test():
            session_id = "async_sess_100"
            await self.memory_manager.store_memory(
                session_id=session_id,
                agent_name="NutritionistAgent",
                key="caloric_target",
                value={"calories": 2800, "protein_g": 180},
                memory_type="short_term"
            )

            recalled = await self.memory_manager.recall_memory(session_id, agent_name="NutritionistAgent")
            self.assertEqual(len(recalled), 1)
            self.assertEqual(recalled[0].key, "caloric_target")
            self.assertEqual(recalled[0].value["calories"], 2800)

            search_res = await self.memory_manager.search_memory(session_id, "2800")
            self.assertEqual(len(search_res), 1)

        asyncio.run(run_memory_test())

    def test_history_compaction(self):
        """Verify context window compaction reduces history while preserving a summary message."""
        async def run_compaction_test():
            session_id = "compact_sess_200"
            messages = [
                AgentMessage(sender=f"Agent_{i}", recipient=f"Agent_{i+1}", message_type=f"STEP_{i}", payload={"step": i})
                for i in range(12)
            ]

            self.assertEqual(len(messages), 12)
            compacted = await self.memory_manager.compact_history_async(session_id, messages, max_messages=5)

            # Compacted history should be reduced to max_messages (5)
            self.assertEqual(len(compacted), 5)
            self.assertEqual(compacted[0].sender, "SystemMemoryManager")
            self.assertEqual(compacted[0].message_type, "COMPACTED_HISTORY_SUMMARY")

            # Memory node for compaction should be created
            nodes = await self.memory_manager.recall_memory(session_id)
            compaction_nodes = [n for n in nodes if n.memory_type == "compacted_summary"]
            self.assertEqual(len(compaction_nodes), 1)

        asyncio.run(run_compaction_test())

    def test_orchestrator_with_database_and_session(self):
        """Verify full orchestrator pipeline with database tracking and session ID."""
        session_id = "orchestrator_sess_300"
        orchestrator = MealPlannerOrchestrator(db_manager=self.db, session_id=session_id)

        input_data = {
            "height": "178 cm",
            "weight": "72 kg",
            "goal": "Build muscle and avoid seafood",
            "age": 27,
            "sex": "male",
            "activity_level": "moderate"
        }

        results = orchestrator.run(input_data)

        self.assertEqual(results["session_id"], session_id)
        self.assertIn("user_profile", results)
        self.assertIn("full_meal_plan", results)

        # Confirm data was saved in SQLite DB
        db_profile = self.db.get_user_profile(session_id)
        self.assertIsNotNone(db_profile)
        self.assertEqual(db_profile.height_cm, 178.0)
        self.assertIn("seafood", db_profile.dietary_exclusions)

        history = self.db.get_interaction_history(session_id)
        self.assertGreater(len(history), 0)


if __name__ == "__main__":
    unittest.main()
