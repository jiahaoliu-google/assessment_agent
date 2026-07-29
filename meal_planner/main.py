"""
Main CLI Application Entry Point for Interactive Terminal Execution.
"""

import sys
import os
from pathlib import Path
from meal_planner.orchestrator import MealPlannerOrchestrator
from meal_planner.utils.export import export_to_markdown
from meal_planner.utils.ui import (
    print_banner, print_box, print_table,
    CYAN, GREEN, YELLOW, MAGENTA, BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_MAGENTA, BOLD, RESET, DIM
)


def get_user_inputs_interactive() -> dict:
    """Prompts the user interactively in the terminal for physical metrics and plain text goal."""
    print(f"\n{BRIGHT_CYAN}{BOLD}📝 STEP 1: USER TELEMETRY & NUTRITIONAL GOALS INPUT{RESET}\n")

    # 1. Height
    while True:
        try:
            h_input = input(f"{BOLD}👉 Enter your Height (e.g., '178 cm', '5ft 10in', or '178'): {RESET}").strip()
            if h_input:
                break
            print(f"{YELLOW}Height is required. Please enter a valid value.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    # 2. Weight
    while True:
        try:
            w_input = input(f"{BOLD}👉 Enter your Weight (e.g., '75 kg', '165 lbs', or '75'): {RESET}").strip()
            if w_input:
                break
            print(f"{YELLOW}Weight is required. Please enter a valid value.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    # 3. Plain Text Goal
    while True:
        try:
            goal_input = input(f"\n{BOLD}👉 Explain your goal in plain text {RESET}{DIM}(e.g., 'Lose weight for summer, build muscle, avoid dairy, high protein'){RESET}:\n> ").strip()
            if goal_input:
                break
            print(f"{YELLOW}Goal description is required. Please explain your target in plain text.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    # Optional Age, Sex, Activity Level with defaults
    print(f"\n{DIM}(Optional Parameters - Press Enter to use defaults){RESET}")
    age_input = input(f"👉 Enter your Age [Default: 28]: ").strip()
    sex_input = input(f"👉 Enter Biological Sex (male/female) [Default: male]: ").strip()
    activity_input = input(f"👉 Enter Activity Level (sedentary/light/moderate/heavy/athlete) [Default: moderate]: ").strip()

    return {
        "height": h_input,
        "weight": w_input,
        "goal": goal_input,
        "age": int(age_input) if age_input.isdigit() else 28,
        "sex": sex_input if sex_input else "male",
        "activity_level": activity_input if activity_input else "moderate"
    }


def render_summary_dashboard(results: dict):
    """Renders the final meal plan summary, 7-day schedule, and grocery list in terminal."""
    user = results["user_profile"]
    target = results["nutrition_target"]
    plan = results["full_meal_plan"]
    audit = results["audit_result"]
    grocery = results["grocery_list"]

    session_id = results.get("session_id", "N/A")

    # 1. Summary Card
    summary_lines = [
        f"Session ID       : {BOLD}{BRIGHT_MAGENTA}{session_id}{RESET} (SQLite Persistent Context & Memory Active)",
        f"Goal Evaluation  : {BOLD}{user.raw_goal}{RESET}",
        f"Goal Category    : {BOLD}{user.parsed_goal_type.upper()}{RESET} (Calorie Adjustment: {user.caloric_target_offset*100:+.0f}%)",
        f"Biometrics       : {user.height_cm} cm | {user.weight_kg} kg | BMI {user.bmi} ({user.bmi_category})",
        f"BMR / TDEE       : {int(target.bmr)} kcal / {int(target.tdee)} kcal",
        f"Target Intake    : {BOLD}{BRIGHT_GREEN}{int(target.target_calories)} kcal / day{RESET}",
        f"Daily Macros     : Protein: {BOLD}{int(target.protein_g)}g{RESET} | Carbs: {BOLD}{int(target.carbs_g)}g{RESET} | Fat: {BOLD}{int(target.fat_g)}g{RESET}",
        f"Hydration Target : {target.water_liters:.1f} Liters of water / day",
        f"Diet Audit Score : {BOLD}{BRIGHT_CYAN}{audit.score} / 100{RESET} ({'PASSED ✅' if audit.passed else 'MODIFIED ⚠️'})"
    ]
    print("\n")
    print_box("🎯 NUTRITIONAL PROFILE & MACRO TARGETS", summary_lines, color=BRIGHT_CYAN, width=80)

    # 2. 7-Day Plan Tables
    print(f"\n{BRIGHT_CYAN}{BOLD}📅 GENERATED 7-DAY MEAL SCHEDULE{RESET}\n")

    for day in plan.daily_plans:
        print(f"\n{BRIGHT_YELLOW}{BOLD}🔹 {day.day_name.upper()} {RESET}{DIM}(Total: {int(day.total_calories)} kcal | P: {int(day.total_protein_g)}g | C: {int(day.total_carbs_g)}g | F: {int(day.total_fat_g)}g){RESET}")
        headers = ["Meal", "Recipe Name", "Calories", "Macros (P / C / F)", "Prep / Cook"]
        rows = []
        for meal in day.meals:
            rows.append([
                meal.meal_type,
                meal.name,
                f"{int(meal.calories)} kcal",
                f"{int(meal.protein_g)}g / {int(meal.carbs_g)}g / {int(meal.fat_g)}g",
                f"{meal.prep_time_mins}m / {meal.cook_time_mins}m"
            ])
        print_table(headers, rows)

    # 3. Categorized Grocery List
    print(f"\n{BRIGHT_GREEN}{BOLD}🛒 CATEGORIZED GROCERY SHOPPING LIST{RESET}\n")
    for cat in grocery.categories:
        print(f"{BOLD}{GREEN}► {cat.category_name.upper()}{RESET}")
        for item in cat.items:
            print(f"  • {item}")
        print()

    # 4. Meal Prep Tips
    print(f"{BRIGHT_MAGENTA}{BOLD}💡 BATCH MEAL PREP STRATEGY & TIPS{RESET}\n")
    for tip in grocery.prep_tips:
        print(f"  ✓ {tip}")
    print()


def main():
    """Main execution function."""
    print_banner()

    # Collect inputs
    user_inputs = get_user_inputs_interactive()

    # Run Multi-Agent System Engine
    orchestrator = MealPlannerOrchestrator()
    results = orchestrator.run(user_inputs)

    # Render Terminal Results
    render_summary_dashboard(results)

    # Export Report Option
    export_choice = input(f"\n{BOLD}💾 Would you like to export this Meal Plan to 'meal_plan_report.md'? (Y/n): {RESET}").strip().lower()
    if export_choice != 'n':
        output_file = "meal_plan_report.md"
        saved_path = export_to_markdown(
            results["full_meal_plan"],
            results["audit_result"],
            results["grocery_list"],
            output_file
        )
        print(f"\n{BRIGHT_GREEN}{BOLD}✨ Meal Plan successfully saved to: {saved_path}{RESET}\n")


if __name__ == "__main__":
    main()
