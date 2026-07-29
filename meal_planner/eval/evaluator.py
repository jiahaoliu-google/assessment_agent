"""
Automated Evaluation Suite Engine for Multi-Agent System Benchmark.
Evaluates agent system output quality against Golden Benchmark Datasets across
Goal Parsing, Exclusion Compliance, Macro Alignment, and Audit Pass Scores.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from meal_planner.orchestrator import MealPlannerOrchestrator
from meal_planner.models import FullMealPlan, AuditResult, UserProfile, NutritionTarget


class EvaluationResult:
    """Container for individual golden persona evaluation metrics."""

    def __init__(
        self,
        eval_id: str,
        persona_name: str,
        passed: bool,
        goal_parsing_passed: bool,
        exclusion_compliance_passed: bool,
        audit_score_passed: bool,
        caloric_accuracy_pct: float,
        audit_score: int,
        details: Dict[str, Any]
    ):
        self.eval_id = eval_id
        self.persona_name = persona_name
        self.passed = passed
        self.goal_parsing_passed = goal_parsing_passed
        self.exclusion_compliance_passed = exclusion_compliance_passed
        self.audit_score_passed = audit_score_passed
        self.caloric_accuracy_pct = caloric_accuracy_pct
        self.audit_score = audit_score
        self.details = details


class AgentSystemEvaluator:
    """
    Automated Benchmark Evaluation Engine that runs the Multi-Agent Meal Planner Orchestrator
    against ground-truth golden datasets and computes quantitative accuracy metrics.
    """

    def __init__(self, golden_dataset_path: str = "evals/golden_dataset.json"):
        self.golden_dataset_path = golden_dataset_path
        self.dataset = self._load_golden_dataset()

    def _load_golden_dataset(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.golden_dataset_path):
            raise FileNotFoundError(f"Golden dataset not found at {self.golden_dataset_path}")
        with open(self.golden_dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_all(self, orchestrator: Optional[MealPlannerOrchestrator] = None) -> Dict[str, Any]:
        """Runs evaluation benchmark across all golden personas in dataset."""
        if not orchestrator:
            orchestrator = MealPlannerOrchestrator(interactive_hitl=False)

        eval_results: List[EvaluationResult] = []

        total_cases = len(self.dataset)
        passed_cases = 0
        sum_audit_scores = 0
        sum_caloric_accuracy = 0.0

        for test_case in self.dataset:
            eval_id = test_case["eval_id"]
            persona = test_case["persona_name"]
            inputs = test_case["inputs"]
            expected = test_case["expected_metrics"]

            logging.info(f"Evaluating Golden Persona '{persona}' ({eval_id})...")

            # Run Orchestrator Pipeline
            pipeline_out = orchestrator.run(inputs)

            user_prof: UserProfile = pipeline_out["user_profile"]
            nut_target: NutritionTarget = pipeline_out["nutrition_target"]
            meal_plan: FullMealPlan = pipeline_out["full_meal_plan"]
            audit_res: AuditResult = pipeline_out["audit_result"]

            # 1. Goal Parsing Evaluation
            goal_parsing_passed = (user_prof.parsed_goal_type == expected["parsed_goal_type"])

            # 2. Exclusion Compliance Evaluation
            mandatory_excls = expected.get("mandatory_exclusions", [])
            exclusion_compliance_passed = True
            missing_excls = []
            for exc in mandatory_excls:
                if exc not in user_prof.dietary_exclusions:
                    exclusion_compliance_passed = False
                    missing_excls.append(exc)

            # 3. Caloric Alignment Accuracy
            target_cal = nut_target.target_calories
            actual_cal = meal_plan.average_daily_calories
            caloric_diff_pct = abs(actual_cal - target_cal) / target_cal * 100.0
            caloric_accuracy_pct = round(max(0.0, 100.0 - caloric_diff_pct), 1)

            # 4. Audit Score Threshold
            min_score = expected.get("min_audit_score", 80)
            audit_score_passed = audit_res.score >= min_score

            case_passed = (
                goal_parsing_passed and
                exclusion_compliance_passed and
                audit_score_passed
            )

            if case_passed:
                passed_cases += 1

            sum_audit_scores += audit_res.score
            sum_caloric_accuracy += caloric_accuracy_pct

            eval_res = EvaluationResult(
                eval_id=eval_id,
                persona_name=persona,
                passed=case_passed,
                goal_parsing_passed=goal_parsing_passed,
                exclusion_compliance_passed=exclusion_compliance_passed,
                audit_score_passed=audit_score_passed,
                caloric_accuracy_pct=caloric_accuracy_pct,
                audit_score=audit_res.score,
                details={
                    "expected_goal": expected["parsed_goal_type"],
                    "parsed_goal": user_prof.parsed_goal_type,
                    "missing_exclusions": missing_excls,
                    "target_calories": target_cal,
                    "actual_calories": actual_cal,
                    "audit_warnings": audit_res.warnings
                }
            )
            eval_results.append(eval_res)

        benchmark_pass_rate = (passed_cases / total_cases) * 100.0 if total_cases > 0 else 0.0
        avg_audit_score = sum_audit_scores / total_cases if total_cases > 0 else 0.0
        avg_caloric_accuracy = sum_caloric_accuracy / total_cases if total_cases > 0 else 0.0

        summary = {
            "total_benchmark_cases": total_cases,
            "passed_cases": passed_cases,
            "benchmark_pass_rate_pct": round(benchmark_pass_rate, 1),
            "average_audit_score": round(avg_audit_score, 1),
            "average_caloric_accuracy_pct": round(avg_caloric_accuracy, 1),
            "detailed_results": [
                {
                    "eval_id": r.eval_id,
                    "persona": r.persona_name,
                    "passed": r.passed,
                    "caloric_accuracy_pct": r.caloric_accuracy_pct,
                    "audit_score": r.audit_score,
                    "details": r.details
                }
                for r in eval_results
            ]
        }

        self._save_eval_report(summary)
        return summary

    def _save_eval_report(self, summary: Dict[str, Any]):
        """Saves evaluation results to JSON and Markdown artifacts."""
        os.makedirs("evals", exist_ok=True)
        json_path = "evals/eval_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        md_path = "evals/eval_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# 📊 Multi-Agent System Golden Benchmark Evaluation Report\n\n")
            f.write(f"- **Total Test Cases**: {summary['total_benchmark_cases']}\n")
            f.write(f"- **Passed Cases**: {summary['passed_cases']} ({summary['benchmark_pass_rate_pct']}% Pass Rate)\n")
            f.write(f"- **Average Quality Audit Score**: {summary['average_audit_score']} / 100\n")
            f.write(f"- **Average Caloric Accuracy**: {summary['average_caloric_accuracy_pct']}%\n\n")
            f.write("## Persona Breakdown\n\n")
            f.write("| Eval ID | Persona | Status | Audit Score | Caloric Accuracy |\n")
            f.write("|---------|---------|--------|-------------|------------------|\n")
            for r in summary["detailed_results"]:
                status = "PASSED ✅" if r["passed"] else "FAILED ❌"
                f.write(f"| {r['eval_id']} | {r['persona']} | {status} | {r['audit_score']} / 100 | {r['caloric_accuracy_pct']}% |\n")
