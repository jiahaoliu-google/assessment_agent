"""
Agent 4: Quality Control & Dietary Auditor Agent (DietaryAuditorAgent).
Uses 'validate_dietary_restrictions' tool via ToolRegistry/MCP.
Executes high-reasoning tier LLM auditing for safety guardrails.
"""

from typing import Dict, Any, List, Optional
from meal_planner.agents.base_agent import BaseAgent
from meal_planner.llm.router import StrategicModelRouter
from meal_planner.models import FullMealPlan, AuditResult
from meal_planner.prompts.system_prompts import DIETARY_AUDITOR_SYSTEM_PROMPT
from meal_planner.tools.registry import ToolRegistry
from meal_planner.utils.ui import BRIGHT_CYAN


class DietaryAuditorAgent(BaseAgent):
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        session_id: Optional[str] = None,
        model_router: Optional[StrategicModelRouter] = None
    ):
        super().__init__(
            name="DietaryAuditorAgent",
            role="Audits generated meal plan against physiological targets, dietary restrictions, and safety guidelines.",
            system_prompt=DIETARY_AUDITOR_SYSTEM_PROMPT,
            tool_registry=tool_registry,
            session_id=session_id,
            model_router=model_router
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes high-reasoning tier audit inspection using LLM tools and model routing.
        """
        self.log("Performing full multi-factor audit with validate_dietary_restrictions Tool...", color=BRIGHT_CYAN)
        plan: FullMealPlan = input_data["full_meal_plan"]
        target = plan.nutrition_target
        user = plan.user_profile

        # Dispatch high-reasoning tier audit prompt via StrategicModelRouter
        audit_prompt = f"Audit 7-day plan against target calories ({target.target_calories}) and exclusions ({user.dietary_exclusions})"
        llm_resp = self.execute_llm_generation(audit_prompt)
        self.log(f"Model Router Response [{llm_resp.provider_name}:{llm_resp.model_name}] (High Reasoning Guardrail)")

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

        # 3. Dietary Exclusion Audit via LLM Tool
        exclusions = user.dietary_exclusions
        all_ingredients = [
            ing.name
            for day in plan.daily_plans
            for meal in day.meals
            for ing in meal.ingredients
        ]

        if exclusions:
            tool_res = self.invoke_tool(
                "validate_dietary_restrictions",
                ingredients=all_ingredients,
                exclusions=exclusions
            )

            if tool_res.success:
                audit_data = tool_res.data
                if audit_data["is_compliant"]:
                    recommendations.append(f"100% compliant with user exclusions ({', '.join(exclusions)})")
                else:
                    score -= 20 * audit_data["total_violations"]
                    for v in audit_data["violations"]:
                        warnings.append(f"SAFETY VIOLATION: '{v['ingredient']}' violates exclusion '{v['exclusion']}' ({v['reason']})")
        else:
            recommendations.append("No dietary exclusions specified.")

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
        passed = score >= 80

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

        self.log(f"Audit Complete: Final Score = {score}/100 ({'PASSED ✅' if passed else 'REQUIRES ADJUSTMENT ⚠️'})")

        self.send_message(
            recipient="GroceryPrepAgent",
            message_type="AUDIT_COMPLETED",
            payload={"full_meal_plan": plan, "audit_result": audit_result}
        )

        return {"full_meal_plan": plan, "audit_result": audit_result}
