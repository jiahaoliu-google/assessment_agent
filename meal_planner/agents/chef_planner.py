"""
Agent 3: Culinary Specialist & Chef Agent (ChefMealPlannerAgent).
Generates a complete, delicious 7-Day Meal Plan scaled precisely to caloric targets.
"""

from typing import Dict, Any, List
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.models import UserProfile, NutritionTarget, DailyMealPlan, FullMealPlan
from meal_planner.utils.nutrition_db import select_recipes_for_plan, scale_meal
from meal_planner.utils.ui import BRIGHT_MAGENTA


DAYS_OF_WEEK = [
    "Day 1 - Monday",
    "Day 2 - Tuesday",
    "Day 3 - Wednesday",
    "Day 4 - Thursday",
    "Day 5 - Friday",
    "Day 6 - Saturday",
    "Day 7 - Sunday"
]


class ChefMealPlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ChefMealPlannerAgent",
            role="Crafts appetizing, varied 7-day culinary recipe plans aligned with exact macro allocations."
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes culinary meal plan generation across 7 days.
        Expects 'user_profile' and 'nutrition_target' in input_data.
        """
        self.log("Assembling 7-Day Culinary Matrix & scaling recipes...", color=BRIGHT_MAGENTA)
        profile: UserProfile = input_data["user_profile"]
        target: NutritionTarget = input_data["nutrition_target"]

        goal = profile.parsed_goal_type
        exclusions = profile.dietary_exclusions

        # Select recipes for each meal category
        breakfast_recipes = select_recipes_for_plan("Breakfast", goal, exclusions, count=7)
        lunch_recipes = select_recipes_for_plan("Lunch", goal, exclusions, count=7)
        dinner_recipes = select_recipes_for_plan("Dinner", goal, exclusions, count=7)
        snack_recipes = select_recipes_for_plan("Snack", goal, exclusions, count=7)

        daily_plans: List[DailyMealPlan] = []

        for day_idx in range(7):
            day_name = DAYS_OF_WEEK[day_idx]
            
            # Target calories per meal
            target_b_cal = target.meal_macro_distribution["Breakfast"]["calories"]
            target_l_cal = target.meal_macro_distribution["Lunch"]["calories"]
            target_d_cal = target.meal_macro_distribution["Dinner"]["calories"]
            target_s_cal = target.meal_macro_distribution["Snack"]["calories"]

            # Scale selected recipes
            b_meal = scale_meal(breakfast_recipes[day_idx], target_b_cal)
            l_meal = scale_meal(lunch_recipes[day_idx], target_l_cal)
            d_meal = scale_meal(dinner_recipes[day_idx], target_d_cal)
            s_meal = scale_meal(snack_recipes[day_idx], target_s_cal)

            daily_plan = DailyMealPlan(
                day_number=day_idx + 1,
                day_name=day_name,
                meals=[b_meal, l_meal, d_meal, s_meal]
            )
            daily_plans.append(daily_plan)

        full_plan = FullMealPlan(
            user_profile=profile,
            nutrition_target=target,
            daily_plans=daily_plans
        )

        self.log(f"Generated 7 Daily Plans ({len(daily_plans)} days, 28 distinct meals prepared)")
        self.log(f"Average Weekly Caloric Density: {int(full_plan.average_daily_calories)} kcal/day (Protein: {int(full_plan.average_daily_protein)}g)")

        self.send_message(
            recipient="DietaryAuditorAgent",
            message_type="MEAL_PLAN_GENERATED",
            payload={"full_meal_plan": full_plan}
        )

        return {"full_meal_plan": full_plan}
