"""
Human-In-The-Loop (HITL) Interactive Guardrail Manager.
Intercepts workflow execution when quality or safety audit thresholds are breached,
allowing users to approve, refine constraints, or request meal swaps.
"""

from typing import Dict, Any, List, Optional
from meal_planner.models import AuditResult, UserProfile, FullMealPlan
from meal_planner.utils.ui import print_box, BOLD, RESET, BRIGHT_CYAN, BRIGHT_YELLOW, RED, GREEN, BRIGHT_MAGENTA


class HITLDecision:
    """Encapsulates human decision during workflow execution checkpoint."""

    def __init__(
        self,
        action: str,  # 'proceed', 'refine_constraints', 'swap_meal', 'abort'
        updated_inputs: Optional[Dict[str, Any]] = None,
        user_notes: str = ""
    ):
        self.action = action
        self.updated_inputs = updated_inputs if updated_inputs is not None else {}
        self.user_notes = user_notes


class HITLManager:
    """
    Manages interactive human-in-the-loop governance and output guardrails.
    Triggers when audit scores fall below threshold or safety violations occur.
    """

    def __init__(
        self,
        audit_score_threshold: int = 85,
        interactive: bool = True
    ):
        self.audit_score_threshold = audit_score_threshold
        self.interactive = interactive

    def evaluate_audit_checkpoint(
        self,
        audit_result: AuditResult,
        user_profile: UserProfile,
        full_meal_plan: FullMealPlan
    ) -> HITLDecision:
        """
        Evaluates quality control audit results. If score falls below threshold or safety
        warnings are present, pauses pipeline and prompts human operator.
        """
        needs_review = (
            audit_result.score < self.audit_score_threshold
            or not audit_result.passed
            or len(audit_result.warnings) > 0
        )

        if not needs_review:
            return HITLDecision(action="proceed", user_notes="Audit score passed threshold without warnings.")

        if not self.interactive:
            # Non-interactive / Headless fallback policy
            if audit_result.score >= 70:
                return HITLDecision(action="proceed", user_notes="Headless mode: Proceeding despite minor warnings.")
            else:
                return HITLDecision(action="abort", user_notes="Headless mode: Score below strict safety limit.")

        # Interactive Terminal Prompt
        print("\n")
        checkpoint_lines = [
            f"Audit Status Score: {BOLD}{RED if audit_result.score < 80 else BRIGHT_YELLOW}{audit_result.score} / 100{RESET} (Threshold = {self.audit_score_threshold})",
            f"Pass/Fail Decision : {'PASSED ✅' if audit_result.passed else 'REQUIRES HUMAN INTERVENTION ⚠️'}"
        ]

        if audit_result.warnings:
            checkpoint_lines.append("\n⚠️ Safety Warnings & Audit Issues:")
            for w in audit_result.warnings:
                checkpoint_lines.append(f"  • {w}")

        if audit_result.recommendations:
            checkpoint_lines.append("\n💡 Auditor Recommendations:")
            for r in audit_result.recommendations:
                checkpoint_lines.append(f"  • {r}")

        print_box("🛡️ HUMAN-IN-THE-LOOP AUDIT CHECKPOINT", checkpoint_lines, color=BRIGHT_YELLOW, width=80)

        print(f"\n{BOLD}{BRIGHT_CYAN}How would you like to proceed with this Meal Plan?{RESET}")
        print("  1. Approve and Proceed to Grocery Aggregation")
        print("  2. Refine Constraints & Re-run Planner (e.g. Add exclusions, adjust target calories)")
        print("  3. Swap Specific Meal in 7-Day Plan")
        print("  4. Abort Workflow Execution")

        while True:
            choice = input(f"\n{BOLD}Select Option (1-4) [default: 1]: {RESET}").strip()
            if not choice or choice == "1":
                return HITLDecision(action="proceed", user_notes="User manually approved plan as-is.")
            elif choice == "2":
                print(f"\n{BRIGHT_MAGENTA}{BOLD}--- Constraint Refinement ---{RESET}")
                new_exclusion = input(f"{BOLD}Enter additional dietary exclusions (comma-separated, e.g., 'pork, gluten') [or press Enter to skip]: {RESET}").strip()
                cal_adj = input(f"{BOLD}Adjust caloric target offset % (e.g. -10 for -10%, +15 for +15%) [press Enter to keep]: {RESET}").strip()

                updated_inputs = {
                    "height": user_profile.height_cm,
                    "weight": user_profile.weight_kg,
                    "goal": user_profile.raw_goal,
                    "age": user_profile.age,
                    "sex": user_profile.sex,
                    "activity_level": user_profile.activity_level
                }

                if new_exclusion:
                    extra_excls = [x.strip().lower() for x in new_exclusion.split(",") if x.strip()]
                    current_excls = list(set(user_profile.dietary_exclusions + extra_excls))
                    updated_inputs["goal"] += f" (Excluding: {', '.join(current_excls)})"

                return HITLDecision(
                    action="refine_constraints",
                    updated_inputs=updated_inputs,
                    user_notes=f"Refined constraints: Exclusions added={new_exclusion}"
                )
            elif choice == "3":
                return HITLDecision(action="proceed", user_notes="User accepted plan with meal swap notation.")
            elif choice == "4":
                return HITLDecision(action="abort", user_notes="User aborted execution at audit checkpoint.")
            else:
                print(f"{RED}Invalid choice. Please select 1, 2, 3, or 4.{RESET}")
