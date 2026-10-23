"""Tests for Flask app integration and route registration."""

import unittest

try:
    from backend.app import app
except ModuleNotFoundError:
    from app import app


class AppIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_oracle_routes_preserved(self):
        """Verify all 19 original Oracle routes remain registered."""
        expected_oracle_routes = {
            ("/", "GET"),
            ("/api/students", "GET"),
            ("/api/students", "POST"),
            ("/api/students/<student_id>", "GET"),
            ("/api/scholarships", "GET"),
            ("/api/scholarships", "POST"),
            ("/api/applications", "GET"),
            ("/api/applications", "POST"),
            ("/api/students/<student_id>/scholarships", "GET"),
            ("/api/applications/<application_id>/status", "PUT"),
            ("/api/disbursements", "GET"),
            ("/api/disbursements", "POST"),
            ("/api/fees", "POST"),
            ("/api/fees", "GET"),
            ("/api/students/<student_id>/fees", "GET"),
            ("/api/payments", "GET"),
            ("/api/payments", "POST"),
            ("/api/students/<student_id>/payments", "GET"),
            ("/api/dashboard", "GET"),
        }

        registered_routes = set()
        for rule in self.app.url_map.iter_rules():
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                registered_routes.add((rule.rule, method))

        for route, method in expected_oracle_routes:
            self.assertIn(
                (route, method),
                registered_routes,
                f"Missing expected Oracle route: {method} {route}",
            )

    def test_neo4j_routes_registered(self):
        """Verify all Neo4j blueprint routes (generic and academic) are registered on the main app."""
        expected_neo4j_routes = {
            ("/api/neo4j/health", "GET"),
            ("/api/neo4j/nodes/<label>", "GET"),
            ("/api/neo4j/nodes/<label>", "POST"),
            ("/api/neo4j/nodes/<label>/<identifier>", "GET"),
            ("/api/neo4j/students", "GET"),
            ("/api/neo4j/students", "POST"),
            ("/api/neo4j/students/<student_id>", "GET"),
            ("/api/neo4j/students/<student_id>/profile", "GET"),
            ("/api/neo4j/students/<student_id>/guardians", "GET"),
            ("/api/neo4j/departments", "GET"),
            ("/api/neo4j/departments/<dept_id>", "GET"),
            ("/api/neo4j/programs", "GET"),
            ("/api/neo4j/programs/<program_id>/students", "GET"),
            ("/api/neo4j/applications", "GET"),
            ("/api/neo4j/applications", "POST"),
            ("/api/neo4j/applications/<application_id>", "GET"),
            ("/api/neo4j/applications/<application_id>/status", "PUT"),
            ("/api/neo4j/students/<student_id>/applications", "GET"),
            ("/api/neo4j/scholarships", "GET"),
            ("/api/neo4j/scholarships", "POST"),
            ("/api/neo4j/scholarships/<scholarship_id>", "GET"),
            ("/api/neo4j/dashboard", "GET"),
            ("/api/neo4j/graph", "GET"),
            ("/api/neo4j/fees", "GET"),
            ("/api/neo4j/fees", "POST"),
            ("/api/neo4j/fees/<fee_id>", "GET"),
            ("/api/neo4j/students/<student_id>/fees", "GET"),
            ("/api/neo4j/payments", "GET"),
            ("/api/neo4j/payments", "POST"),
            ("/api/neo4j/payments/<payment_id>", "GET"),
            ("/api/neo4j/students/<student_id>/payments", "GET"),
            ("/api/neo4j/disbursements", "GET"),
            ("/api/neo4j/disbursements", "POST"),
            ("/api/neo4j/disbursements/<disbursement_id>", "GET"),
            ("/api/neo4j/bank-accounts", "GET"),
            ("/api/neo4j/bank-accounts", "POST"),
            ("/api/neo4j/bank-accounts/<account_no>", "GET"),
            ("/api/neo4j/students/<student_id>/scholarships", "GET"),
        }

        registered_routes = set()
        for rule in self.app.url_map.iter_rules():
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                registered_routes.add((rule.rule, method))

        for route, method in expected_neo4j_routes:
            self.assertIn(
                (route, method),
                registered_routes,
                f"Missing expected Neo4j route: {method} {route}",
            )

    def test_home_endpoint(self):
        """Verify the root endpoint responds with application running message."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("Scholarship and Fee Management System API is running", data["message"])


if __name__ == "__main__":
    unittest.main()
