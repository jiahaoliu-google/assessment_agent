"""
Agent 4: Quality Control & Dietary Auditor Agent (DietaryAuditorAgent).
Performs clinical nutritional verification, exclusion safety checks, and macro precision scoring.
"""

from typing import Dict, Any, List
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.models import FullMealPlan, AuditResult
from meal_planner.utils.ui import BRIGHT_CYAN


class DietaryAuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DietaryAuditorAgent",
            role="Audits generated meal plan against physiological targets, dietary restrictions, and safety guidelines."
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes audit inspection.
        Expects 'full_meal_plan' in input_data.
        """
        self.log("Performing full multi-factor clinical audit on 7-day meal schedule...", color=BRIGHT_CYAN)
        plan: FullMealPlan = input_data["full_meal_plan"]
        target = plan.nutrition_target
        user = plan.user_profile

        warnings: List[str] = []
        recommendations: List[str] = []
        score = 100

        # 1. Caloric Variance Audit
        avg_cal = plan.average_daily_calories
        target_cal = target.target_calories
        cal_diff_pct = abs(avg_cal - target_cal) / target_cal * 100.0

        if cal_diff_pct > 5.0:
            score -= 10
            warnings.append(f"Caloric variance is {cal_diff_pct:.1f}% from target ({int(avg_cal)} vs {int(target_cal)} kcal)")
        else:
            recommendations.append(f"Caloric alignment is optimal (within {cal_diff_pct:.1f}% of target)")

        # 2. Protein Audit
        avg_p = plan.average_daily_protein
        target_p = target.protein_g
        p_diff_pct = abs(avg_p - target_p) / target_p * 100.0

        if p_diff_pct > 8.0:
            score -= 5
            warnings.append(f"Protein intake variance is {p_diff_pct:.1f}% ({int(avg_p)}g vs target {int(target_p)}g)")

        # 3. Dietary Exclusion Audit
        exclusions = user.dietary_exclusions
        exclusion_violations = 0

        for day in plan.daily_plans:
            for meal in day.meals:
                meal_str = (meal.name + " " + " ".join(i.name for i in meal.ingredients)).lower()
                for exc in exclusions:
                    if exc.lower() in meal_str:
                        score -= 20
                        exclusion_violations += 1
                        warnings.append(f"CRITICAL SAFETY WARNING: Ingredient containing '{exc}' detected in {meal.meal_type} '{meal.name}' on {day.day_name}")

        if exclusion_violations == 0 and exclusions:
            recommendations.append(f"100% compliant with user exclusions ({', '.join(exclusions)})")

        # 4. Variety & Balance Audit
        unique_meals = len(set(m.name for d in plan.daily_plans for m in d.meals))
        total_meals = len(plan.daily_plans) * 4
        variety_ratio = unique_meals / total_meals

        if variety_ratio >= 0.5:
            recommendations.append(f"High culinary variety ({unique_meals} unique meals across 28 servings)")
        else:
            score -= 5
            warnings.append("Meal variety could be increased across consecutive days")

        score = max(0, min(100, score))
        passed = score >= 80 and exclusion_violations == 0

        audit_result = AuditResult(
            score=score,
            passed=passed,
            warnings=warnings,
            recommendations=recommendations,
            macro_variances={
                "calories_variance_pct": round(cal_diff_pct, 1),
                "protein_variance_pct": round(p_diff_pct, 1)
            }
        )

        self.log(f"Audit Complete: Final Score = {score}/100 ({'PASSED' if passed else 'REQUIRES ADJUSTMENT'})")
        for rec in recommendations:
            self.log(f"  ✓ {rec}")
        for w in warnings:
            self.log(f"  ⚠️ {w}")

        self.send_message(
            recipient="GroceryPrepAgent",
            message_type="AUDIT_COMPLETED",
            payload={"full_meal_plan": plan, "audit_result": audit_result}
        )

        return {"full_meal_plan": plan, "audit_result": audit_result}
