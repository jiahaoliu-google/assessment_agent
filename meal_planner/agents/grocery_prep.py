"""
Agent 5: Shopping List & Meal Prep Specialist Agent (GroceryPrepAgent).
Consolidates all recipe ingredients into a categorized grocery list and generates prep guidance.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.models import FullMealPlan, GroceryList, GroceryCategory
from meal_planner.prompts.system_prompts import GROCERY_PREP_SYSTEM_PROMPT
from meal_planner.tools.registry import ToolRegistry
from meal_planner.utils.ui import BRIGHT_GREEN


class GroceryPrepAgent(BaseAgent):
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        session_id: Optional[str] = None
    ):
        super().__init__(
            name="GroceryPrepAgent",
            role="Aggregates weekly recipe ingredients into a categorized grocery shopping list and batch prep guide.",
            system_prompt=GROCERY_PREP_SYSTEM_PROMPT,
            tool_registry=tool_registry,
            session_id=session_id
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes grocery consolidation and meal prep synthesis.
        Expects 'full_meal_plan' in input_data.
        """
        self.log("Aggregating ingredients & compiling categorized weekly grocery shopping list...", color=BRIGHT_GREEN)
        plan: FullMealPlan = input_data["full_meal_plan"]

        # Map to combine quantities: (name, unit, category) -> total_amount
        ingredient_totals = defaultdict(float)
        ingredient_meta = {}

        for day in plan.daily_plans:
            for meal in day.meals:
                for ing in meal.ingredients:
                    key = (ing.name.strip(), ing.unit.strip(), ing.category.strip())
                    ingredient_totals[key] += ing.amount
                    ingredient_meta[key] = (ing.name, ing.unit, ing.category)

        # Categorize
        categories_dict = defaultdict(list)
        for (name, unit, category), total_amt in ingredient_totals.items():
            if total_amt == int(total_amt):
                amt_str = str(int(total_amt))
            else:
                amt_str = f"{total_amt:.1f}"

            item_line = f"{name}: {amt_str} {unit}".strip()
            categories_dict[category].append(item_line)

        grocery_categories: List[GroceryCategory] = []
        for cat_name, items in categories_dict.items():
            items.sort()
            grocery_categories.append(GroceryCategory(category_name=cat_name, items=items))

        # Sort categories logically
        cat_order = ["Produce", "Proteins", "Grains & Complex Carbs", "Dairy & Alternatives", "Healthy Fats & Seeds", "Oils & Condiments", "Spices & Seasonings", "Pantry Staples"]
        grocery_categories.sort(key=lambda c: cat_order.index(c.category_name) if c.category_name in cat_order else 99)

        # Generate Meal Prep Guidance
        prep_tips = [
            "Sunday Batch Prep: Cook complex grains (quinoa, wild rice, sweet potatoes) in advance for Days 1-4.",
            "Protein Marinades: Portion chicken breast and pork tenderloin into sealed glass containers with lemon/herbs.",
            "Fresh Greens Storage: Line salad containers with paper towels to maintain crispness for up to 7 days.",
            "Hydration Station: Keep a 1-liter reusable bottle ready to meet your daily hydration target.",
            "Snack Readiness: Portion out nuts, seeds, and cottage cheese servings into grab-and-go containers."
        ]

        grocery_list = GroceryList(categories=grocery_categories, prep_tips=prep_tips)

        self.log(f"Grocery List Aggregated: {sum(len(c.items) for c in grocery_categories)} total unique items across {len(grocery_categories)} sections.")
        self.log("Batch Meal Prep Strategy generated successfully.")

        return {"full_meal_plan": plan, "grocery_list": grocery_list}
