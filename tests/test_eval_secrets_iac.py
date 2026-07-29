"""
Unit tests for SecretManager, Golden Benchmark Evaluator, and IaC File Structure.
"""

import os
import unittest
from meal_planner.utils.secrets import SecretManager
from meal_planner.eval.evaluator import AgentSystemEvaluator


class TestSecretManager(unittest.TestCase):

    def test_secret_resolution_env(self):
        """Tests resolving secrets from environment variables."""
        os.environ["TEST_SECRET_KEY"] = "secret_value_12345"
        val = SecretManager.get_secret("TEST_SECRET_KEY")
        self.assertEqual(val, "secret_value_12345")
        del os.environ["TEST_SECRET_KEY"]

    def test_secret_resolution_file_fallback(self):
        """Tests resolving secret from local file query."""
        os.makedirs(".secrets", exist_ok=True)
        file_path = ".secrets/jwt_test_secret.txt"
        with open(file_path, "w") as f:
            f.write("file_secret_998877")

        val = SecretManager.get_secret("JWT_TEST_SECRET")
        self.assertEqual(val, "file_secret_998877")

        if os.path.exists(file_path):
            os.remove(file_path)

    def test_secret_resolution_ephemeral_fallback(self):
        """Tests generating cryptographically secure token when secret is unconfigured."""
        val = SecretManager.get_secret("UNCONFIGURED_RANDOM_SECRET_KEY_123")
        self.assertIsNotNone(val)
        self.assertEqual(len(val), 64)  # 32 bytes hex = 64 characters


class TestAgentSystemEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = AgentSystemEvaluator(golden_dataset_path="evals/golden_dataset.json")

    def test_golden_dataset_evaluation(self):
        """Runs automated evaluation suite against golden dataset personas."""
        report = self.evaluator.evaluate_all()
        self.assertIn("total_benchmark_cases", report)
        self.assertGreaterEqual(report["total_benchmark_cases"], 4)
        self.assertIn("benchmark_pass_rate_pct", report)
        self.assertGreaterEqual(report["benchmark_pass_rate_pct"], 75.0)
        self.assertTrue(os.path.exists("evals/eval_report.json"))
        self.assertTrue(os.path.exists("evals/eval_report.md"))


class TestIaCManifests(unittest.TestCase):

    def test_iac_files_exist(self):
        """Verifies that Infrastructure as Code manifests exist and are non-empty."""
        self.assertTrue(os.path.exists("iac/terraform/main.tf"))
        self.assertTrue(os.path.exists("iac/terraform/variables.tf"))
        self.assertTrue(os.path.exists("iac/docker/Dockerfile"))
        self.assertTrue(os.path.exists("iac/docker/docker-compose.yml"))


if __name__ == "__main__":
    unittest.main()
