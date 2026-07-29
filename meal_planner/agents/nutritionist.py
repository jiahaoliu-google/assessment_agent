"""
Agent 2: Nutritionist & Calorie Planner Agent (NutritionistAgent).
Calculates BMR, TDEE, macro ratios, hydration targets, and dietary guidelines.
"""

from typing import Dict, Any
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.models import UserProfile, NutritionTarget
from meal_planner.utils.ui import BRIGHT_YELLOW


class NutritionistAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="NutritionistAgent",
            role="Calculates exact metabolic energy expenditures (BMR, TDEE) and optimal macronutrient distributions."
        )

    def calculate_bmr(self, profile: UserProfile) -> float:
        """Calculates Basal Metabolic Rate using the Mifflin-St Jeor equation."""
        w = profile.weight_kg
        h = profile.height_cm
        a = profile.age

        if profile.sex.lower() == "female":
            bmr = 10 * w + 6.25 * h - 5 * a - 161
        else:
            # Male / Other default
            bmr = 10 * w + 6.25 * h - 5 * a + 5

        return round(bmr, 1)

    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Multiplies BMR by physical activity multiplier to determine TDEE."""
        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "heavy": 1.725,
            "athlete": 1.9
        }
        mult = multipliers.get(activity_level.lower(), 1.55)
        return round(bmr * mult, 1)

    def calculate_macros(self, profile: UserProfile, target_calories: float) -> Tuple_Macros: # type hint
        pass

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes nutritional logic.
        Expects input_data to contain 'user_profile'.
        """
        self.log("Computing clinical energy equations & macro allocations...", color=BRIGHT_YELLOW)
        profile: UserProfile = input_data["user_profile"]

        bmr = self.calculate_bmr(profile)
        tdee = self.calculate_tdee(bmr, profile.activity_level)

        # Target calories
        target_calories = tdee * (1.0 + profile.caloric_target_offset)
        # Enforce healthy lower bound (1200 kcal min)
        target_calories = max(1200.0, round(target_calories, 1))

        # Determine Protein (g)
        goal = profile.parsed_goal_type
        if goal in ["muscle_gain", "recomposition", "weight_loss"]:
            protein_g_per_kg = 2.0  # 2.0g per kg of body weight
        elif "high-protein" in profile.diet_preferences:
            protein_g_per_kg = 2.2
        else:
            protein_g_per_kg = 1.6

        protein_g = min(round(profile.weight_kg * protein_g_per_kg, 1), target_calories * 0.40 / 4.0)
        protein_calories = protein_g * 4.0

        # Determine Fat & Carbs
        if goal == "keto" or "keto" in profile.diet_preferences:
            fat_calories = target_calories * 0.70
            carbs_calories = target_calories * 0.05
            protein_calories = target_calories * 0.25
            protein_g = round(protein_calories / 4.0, 1)
            fat_g = round(fat_calories / 9.0, 1)
            carbs_g = round(carbs_calories / 4.0, 1)
        else:
            fat_calories = target_calories * 0.28
            fat_g = round(fat_calories / 9.0, 1)
            carbs_calories = max(0.0, target_calories - (protein_calories + fat_calories))
            carbs_g = round(carbs_calories / 4.0, 1)

        # Fiber and Hydration
        fiber_g = round(max(25.0, target_calories / 1000.0 * 14.0), 1)
        water_liters = round((profile.weight_kg * 0.035) + 0.5, 1)

        # Meal Macro Allocations (Breakfast 25%, Lunch 35%, Dinner 30%, Snack 10%)
        meal_macro_dist = {
            "Breakfast": {"calories": round(target_calories * 0.25, 1), "protein": round(protein_g * 0.25, 1)},
            "Lunch": {"calories": round(target_calories * 0.35, 1), "protein": round(protein_g * 0.35, 1)},
            "Dinner": {"calories": round(target_calories * 0.30, 1), "protein": round(protein_g * 0.30, 1)},
            "Snack": {"calories": round(target_calories * 0.10, 1), "protein": round(protein_g * 0.10, 1)},
        }

        micronutrient_focus = ["Magnesium", "Zinc", "Vitamin D3", "Omega-3 Fatty Acids", "Electrolytes"]

        nutrition_target = NutritionTarget(
            bmr=bmr,
            tdee=tdee,
            target_calories=target_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
            water_liters=water_liters,
            meal_macro_distribution=meal_macro_dist,
            micronutrient_focus=micronutrient_focus
        )

        self.log(f"Metabolic Calculations: BMR={int(bmr)} kcal, TDEE={int(tdee)} kcal")
        self.log(f"Daily Target Caloric Intake: {int(target_calories)} kcal/day")
        self.log(f"Macros: Protein={int(protein_g)}g ({(protein_calories/target_calories)*100:.0f}%), Carbs={int(carbs_g)}g ({(carbs_calories/target_calories)*100:.0f}%), Fat={int(fat_g)}g ({(fat_calories/target_calories)*100:.0f}%)")

        self.send_message(
            recipient="ChefMealPlannerAgent",
            message_type="NUTRITION_TARGET_READY",
            payload={"user_profile": profile, "nutrition_target": nutrition_target}
        )

        return {"user_profile": profile, "nutrition_target": nutrition_target}
