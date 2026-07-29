"""
Unit tests for Strategic Model Router and Human-In-The-Loop (HITL) Guardrail Manager.
"""

import unittest
from meal_planner.llm.provider import (
    ModelTier, MockLLMProvider, GeminiLLMProvider, OpenAILLMProvider, LLMResponse
)
from meal_planner.llm.router import StrategicModelRouter
from meal_planner.hitl.manager import HITLManager, HITLDecision
from meal_planner.models import AuditResult, UserProfile, FullMealPlan, DailyMealPlan, NutritionTarget
from meal_planner.orchestrator import MealPlannerOrchestrator


class TestStrategicModelRouter(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MockLLMProvider()
        self.router = StrategicModelRouter(primary_provider=self.mock_provider)

    def test_agent_tier_mapping(self):
        """Tests that agents are mapped to appropriate complexity model tiers."""
        self.assertEqual(self.router.get_tier_for_agent("ProfileAnalyzerAgent"), ModelTier.FAST)
        self.assertEqual(self.router.get_tier_for_agent("NutritionistAgent"), ModelTier.BALANCED)
        self.assertEqual(self.router.get_tier_for_agent("ChefMealPlannerAgent"), ModelTier.BALANCED)
        self.assertEqual(self.router.get_tier_for_agent("DietaryAuditorAgent"), ModelTier.REASONING)
        self.assertEqual(self.router.get_tier_for_agent("GroceryPrepAgent"), ModelTier.FAST)

    def test_route_and_generate_mock_fallback(self):
        """Tests that routing and generation returns valid LLMResponse."""
        resp = self.router.route_and_generate(
            agent_name="DietaryAuditorAgent",
            prompt="Audit safety of recipes",
            system_prompt="You are a strict safety auditor."
        )
        self.assertIsInstance(resp, LLMResponse)
        self.assertEqual(resp.provider_name, "MockLLM")
        self.assertIn("mock-reasoning-model", resp.model_name)

    def test_provider_fallback_chain(self):
        """Tests that router falls back to MockLLM when primary provider fails."""
        class FailingProvider(MockLLMProvider):
            def generate(self, *args, **kwargs):
                raise RuntimeError("Simulated Provider Outage")

        failing = FailingProvider()
        router = StrategicModelRouter(primary_provider=failing)
        resp = router.route_and_generate("ProfileAnalyzerAgent", "Test prompt")
        self.assertEqual(resp.provider_name, "MockLLM")


class TestHITLManager(unittest.TestCase):

    def setUp(self):
        self.hitl_headless = HITLManager(audit_score_threshold=85, interactive=False)
        self.dummy_profile = UserProfile(
            height_cm=178, weight_kg=75, age=28, sex="male", activity_level="moderate",
            raw_goal="Build muscle", parsed_goal_type="muscle_gain", caloric_target_offset=0.15,
            diet_preferences=["high-protein"], dietary_exclusions=["pork"]
        )
        self.dummy_target = NutritionTarget(
            bmr=1700, tdee=2600, target_calories=3000, protein_g=150, carbs_g=400, fat_g=90,
            fiber_g=30, water_liters=3.0, meal_macro_distribution={}, micronutrient_focus=[]
        )
        self.dummy_plan = FullMealPlan(
            user_profile=self.dummy_profile, nutrition_target=self.dummy_target, daily_plans=[]
        )

    def test_checkpoint_pass_above_threshold(self):
        """Tests that HITL decision proceeds automatically when audit score >= threshold."""
        passing_audit = AuditResult(score=95, passed=True, warnings=[], recommendations=[])
        decision = self.hitl_headless.evaluate_audit_checkpoint(
            audit_result=passing_audit,
            user_profile=self.dummy_profile,
            full_meal_plan=self.dummy_plan
        )
        self.assertEqual(decision.action, "proceed")

    def test_checkpoint_headless_policy_minor_warnings(self):
        """Tests headless policy behavior when audit score has minor warnings."""
        minor_audit = AuditResult(score=75, passed=False, warnings=["Minor calorie variance"], recommendations=[])
        decision = self.hitl_headless.evaluate_audit_checkpoint(
            audit_result=minor_audit,
            user_profile=self.dummy_profile,
            full_meal_plan=self.dummy_plan
        )
        self.assertEqual(decision.action, "proceed")
        self.assertIn("Headless mode", decision.user_notes)

    def test_checkpoint_headless_policy_severe_failure(self):
        """Tests headless policy abort behavior when audit score falls below safety limit."""
        failing_audit = AuditResult(score=50, passed=False, warnings=["Multiple allergen violations"], recommendations=[])
        decision = self.hitl_headless.evaluate_audit_checkpoint(
            audit_result=failing_audit,
            user_profile=self.dummy_profile,
            full_meal_plan=self.dummy_plan
        )
        self.assertEqual(decision.action, "abort")


class TestOrchestratorLLMAndHITL(unittest.TestCase):

    def test_orchestrator_execution_with_llm_and_hitl(self):
        """Tests end-to-end orchestrator run with StrategicModelRouter and HITLManager."""
        router = StrategicModelRouter(primary_provider=MockLLMProvider())
        hitl = HITLManager(interactive=False)
        orchestrator = MealPlannerOrchestrator(model_router=router, hitl_manager=hitl)

        user_inputs = {
            "height": 180,
            "weight": 75,
            "goal": "Build lean muscle and maintain energy",
            "age": 25,
            "sex": "male",
            "activity_level": "moderate"
        }

        results = orchestrator.run(user_inputs)
        self.assertEqual(results["status"], "completed")
        self.assertIn("session_id", results)
        self.assertGreaterEqual(results["audit_result"].score, 80)


if __name__ == "__main__":
    unittest.main()
