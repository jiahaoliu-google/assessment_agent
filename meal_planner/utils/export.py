"""
Export module for saving meal plans to Markdown and JSON formats.
"""

import json
from pathlib import Path
from meal_planner.models import FullMealPlan, AuditResult, GroceryList


def export_to_markdown(meal_plan: FullMealPlan, audit: AuditResult, grocery: GroceryList, output_path: str) -> str:
    """Exports full 7-day meal plan and shopping guide to a clean Markdown file."""
    user = meal_plan.user_profile
    target = meal_plan.nutrition_target

    md = []
    md.append(f"# 7-Day Personalized Meal Plan Report\n")
    md.append(f"**Generated for Goal:** {user.raw_goal}\n")
    
    # Profile & Macros Summary Table
    md.append("## 👤 User Telemetry & Caloric Targets\n")
    md.append("| Parameter | Value | Notes |")
    md.append("|---|---|---|")
    md.append(f"| **Height** | {user.height_cm} cm | |")
    md.append(f"| **Weight** | {user.weight_kg} kg | |")
    md.append(f"| **BMI** | {user.bmi} | Category: {user.bmi_category} |")
    md.append(f"| **BMR (Basal)** | {int(target.bmr)} kcal/day | Mifflin-St Jeor |")
    md.append(f"| **TDEE (Maintenance)** | {int(target.tdee)} kcal/day | Activity Adjusted |")
    md.append(f"| **Target Daily Intake** | **{int(target.target_calories)} kcal/day** | Goal Adjustment |")
    md.append(f"| **Protein** | {int(target.protein_g)} g ({int(target.protein_g * 4)} kcal) | ~{(target.protein_g * 4 / target.target_calories)*100:.0f}% of total |")
    md.append(f"| **Carbohydrates** | {int(target.carbs_g)} g ({int(target.carbs_g * 4)} kcal) | ~{(target.carbs_g * 4 / target.target_calories)*100:.0f}% of total |")
    md.append(f"| **Fats** | {int(target.fat_g)} g ({int(target.fat_g * 9)} kcal) | ~{(target.fat_g * 9 / target.target_calories)*100:.0f}% of total |")
    md.append(f"| **Hydration Target** | {target.water_liters:.1f} Liters/day | |")
    md.append("\n---\n")

    # Audit Summary
    md.append(f"## 🛡️ Dietary Audit Report (Score: {audit.score}/100)\n")
    md.append(f"- **Status:** {'✅ PASSED' if audit.passed else '⚠️ MODIFIED'}")
    if audit.warnings:
        md.append("- **Audit Notes:**")
        for w in audit.warnings:
            md.append(f"  - {w}")
    if audit.recommendations:
        md.append("- **Recommendations:**")
        for r in audit.recommendations:
            md.append(f"  - {r}")
    md.append("\n---\n")

    # 7-Day Plan Breakdown
    md.append("## 📅 7-Day Meal Schedule\n")
    for day in meal_plan.daily_plans:
        md.append(f"### {day.day_name}")
        md.append(f"**Daily Totals:** {int(day.total_calories)} kcal | Protein: {int(day.total_protein_g)}g | Carbs: {int(day.total_carbs_g)}g | Fat: {int(day.total_fat_g)}g\n")
        
        for meal in day.meals:
            md.append(f"#### 🍽️ {meal.meal_type}: {meal.name}")
            md.append(f"*{int(meal.calories)} kcal | P: {int(meal.protein_g)}g | C: {int(meal.carbs_g)}g | F: {int(meal.fat_g)}g | Prep: {meal.prep_time_mins}m | Cook: {meal.cook_time_mins}m*")
            md.append("\n**Ingredients:**")
            for ing in meal.ingredients:
                md.append(f"- {ing}")
            md.append("\n**Preparation:**")
            for idx, inst in enumerate(meal.instructions, 1):
                md.append(f"{idx}. {inst}")
            md.append("")
        md.append("---\n")

    # Grocery List
    md.append("## 🛒 Categorized Grocery Shopping List\n")
    for cat in grocery.categories:
        md.append(f"### {cat.category_name}")
        for item in cat.items:
            md.append(f"- [ ] {item}")
        md.append("")

    # Meal Prep Tips
    md.append("## 🍳 Meal Prep & Storage Strategy\n")
    for tip in grocery.prep_tips:
        md.append(f"- {tip}")

    content = "\n".join(md)
    path = Path(output_path)
    path.write_text(content, encoding="utf-8")
    return str(path.absolute())
