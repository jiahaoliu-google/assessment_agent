"""
Unit tests for agents and orchestrator workflow.
"""

import unittest
from meal_planner.models import UserProfile, NutritionTarget, FullMealPlan
from meal_planner.agents.profile_analyzer import ProfileAnalyzerAgent
from meal_planner.agents.nutritionist import NutritionistAgent
from meal_planner.agents.chef_planner import ChefMealPlannerAgent
from meal_planner.agents.dietary_auditor import DietaryAuditorAgent
from meal_planner.agents.grocery_prep import GroceryPrepAgent
from meal_planner.orchestrator import MealPlannerOrchestrator


class TestMultiAgentMealPlanner(unittest.TestCase):

    def setUp(self):
        self.profile_agent = ProfileAnalyzerAgent()
        self.nutritionist_agent = NutritionistAgent()
        self.chef_agent = ChefMealPlannerAgent()
        self.auditor_agent = DietaryAuditorAgent()
        self.grocery_agent = GroceryPrepAgent()
        self.orchestrator = MealPlannerOrchestrator()

    def test_profile_analyzer_parsing(self):
        # Test height parsing
        self.assertEqual(self.profile_agent.parse_height("180cm"), 180.0)
        self.assertEqual(self.profile_agent.parse_height("5ft 10in"), 177.8)
        self.assertEqual(self.profile_agent.parse_height("1.75 m"), 175.0)

        # Test weight parsing
        self.assertEqual(self.profile_agent.parse_weight("80kg"), 80.0)
        self.assertAlmostEqual(self.profile_agent.parse_weight("165 lbs"), 74.8, delta=0.5)

        # Test goal evaluation
        goal_type, cal_offset, prefs, excls = self.profile_agent.analyze_goal(
            "I want to lose weight, gain muscle, avoid dairy and nuts, and eat high protein"
        )
        self.assertIn(goal_type, ["weight_loss", "muscle_gain"])
        self.assertIn("dairy", excls)
        self.assertIn("nuts", excls)
        self.assertIn("high-protein", prefs)

    def test_nutritionist_agent_calculations(self):
        profile = UserProfile(
            height_cm=180.0,
            weight_kg=75.0,
            age=25,
            sex="male",
            activity_level="moderate",
            raw_goal="Gain lean muscle",
            parsed_goal_type="muscle_gain",
            caloric_target_offset=0.15
        )

        res = self.nutritionist_agent.process({"user_profile": profile})
        target: NutritionTarget = res["nutrition_target"]

        self.assertGreater(target.bmr, 1500)
        self.assertGreater(target.tdee, target.bmr)
        self.assertGreater(target.target_calories, target.tdee)
        self.assertGreater(target.protein_g, 100.0)

    def test_full_orchestrator_pipeline(self):
        input_data = {
            "height": "175 cm",
            "weight": "70 kg",
            "goal": "Build lean muscle mass, workout 4 times a week, prefer high protein, no dairy",
            "age": 26,
            "sex": "male",
            "activity_level": "heavy"
        }

        results = self.orchestrator.run(input_data)

        self.assertIn("user_profile", results)
        self.assertIn("nutrition_target", results)
        self.assertIn("full_meal_plan", results)
        self.assertIn("audit_result", results)
        self.assertIn("grocery_list", results)

        full_plan: FullMealPlan = results["full_meal_plan"]
        self.assertEqual(len(full_plan.daily_plans), 7)
        for day in full_plan.daily_plans:
            self.assertEqual(len(day.meals), 4)

        audit = results["audit_result"]
        self.assertTrue(audit.passed)
        self.assertGreaterEqual(audit.score, 80)

        grocery = results["grocery_list"]
        self.assertGreater(len(grocery.categories), 0)


if __name__ == "__main__":
    unittest.main()
