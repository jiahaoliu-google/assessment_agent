"""
Agent 2: Nutritionist & Calorie Planner Agent (NutritionistAgent).
Uses 'calculate_tdee_and_macros' tool via ToolRegistry/MCP.
"""

from typing import Dict, Any, Optional
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.llm.router import StrategicModelRouter
from meal_planner.models import UserProfile, NutritionTarget
from meal_planner.prompts.system_prompts import NUTRITIONIST_SYSTEM_PROMPT
from meal_planner.tools.registry import ToolRegistry
from meal_planner.utils.ui import BRIGHT_YELLOW


class NutritionistAgent(BaseAgent):
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        session_id: Optional[str] = None,
        model_router: Optional[StrategicModelRouter] = None
    ):
        super().__init__(
            name="NutritionistAgent",
            role="Calculates exact metabolic energy expenditures (BMR, TDEE) and optimal macronutrient distributions using clinical tools.",
            system_prompt=NUTRITIONIST_SYSTEM_PROMPT,
            tool_registry=tool_registry,
            session_id=session_id,
            model_router=model_router
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes nutritional calculation via tool invocation.
        """
        self.log("Computing clinical energy equations & macro allocations via MCP Tool...", color=BRIGHT_YELLOW)
        profile: UserProfile = input_data["user_profile"]

        # Strategic model router dispatch
        llm_resp = self.execute_llm_generation(f"Synthesize nutritional target parameters for goal: {profile.parsed_goal_type}")
        self.log(f"Model Router Response [{llm_resp.provider_name}:{llm_resp.model_name}]")

        # Invoke Tool: calculate_tdee_and_macros
        tool_res = self.invoke_tool(
            "calculate_tdee_and_macros",
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal_type=profile.parsed_goal_type
        )

        if tool_res.success:
            data = tool_res.data
            bmr = data["bmr_kcal"]
            tdee = data["tdee_kcal"]
            target_calories = data["target_calories_kcal"]
            protein_g = data["protein_g"]
            carbs_g = data["carbs_g"]
            fat_g = data["fat_g"]
            water_liters = data["water_liters"]
        else:
            # Fallback calculation if tool fails
            self.log("Tool invocation failed, engaging fallback calculation engine...", color=BRIGHT_YELLOW)
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
            tdee = bmr * 1.55
            target_calories = tdee * (1.0 + profile.caloric_target_offset)
            protein_g = profile.weight_kg * 2.0
            fat_g = target_calories * 0.28 / 9.0
            carbs_g = (target_calories - (protein_g * 4.0 + fat_g * 9.0)) / 4.0
            water_liters = (profile.weight_kg * 0.035) + 0.5

        fiber_g = round(max(25.0, target_calories / 1000.0 * 14.0), 1)

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
        self.log(f"Macros: Protein={int(protein_g)}g, Carbs={int(carbs_g)}g, Fat={int(fat_g)}g")

        self.send_message(
            recipient="ChefMealPlannerAgent",
            message_type="NUTRITION_TARGET_READY",
            payload={"user_profile": profile, "nutrition_target": nutrition_target}
        )

        return {"user_profile": profile, "nutrition_target": nutrition_target}
