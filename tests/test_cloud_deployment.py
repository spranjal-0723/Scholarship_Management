"""Tests for Render cloud deployment readiness, health probes, and cloud mode routing."""

import unittest
from unittest.mock import patch

try:
    from backend.app import app
except ModuleNotFoundError:
    from app import app


class CloudDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_liveness_probes(self):
        """Verify Render lightweight health check endpoints return 200 OK."""
        for path in ["/healthz", "/render-health"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, f"{path} did not return 200")
            data = response.get_json()
            self.assertEqual(data.get("status"), "live")
            self.assertIn("service", data)
            self.assertIn("mode", data)

    def test_config_endpoint(self):
        """Verify the /api/config endpoint provides runtime configuration."""
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("database_mode", data)
        self.assertIn("read_only", data)
        self.assertIn("neo4j_enabled", data)
        self.assertIn("oracle_enabled", data)

    def test_serve_ui_and_html_accept(self):
        """Verify HTML is served for /app and for / with Accept: text/html."""
        res_app = self.client.get("/app")
        self.assertEqual(res_app.status_code, 200)
        self.assertIn("text/html", res_app.headers.get("Content-Type", ""))
        self.assertIn(b"Scholarship and Fee Management System", res_app.data)

        res_home_html = self.client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
        self.assertEqual(res_home_html.status_code, 200)
        self.assertIn(b"Scholarship and Fee Management System", res_home_html.data)

    def test_cloud_mode_routing_delegation(self):
        """Verify that when APP_DATABASE_MODE is 'neo4j', endpoints route to Neo4j handlers."""
        with self.app.app_context():
            from flask import jsonify
            mock_res = jsonify({"students": [{"studentId": "S1001", "name": "Arjun Sharma"}]})

        with patch("backend.app.APP_DATABASE_MODE", "neo4j"):
            with patch("backend.app.api_list_students", return_value=mock_res) as mock_list_students:
                response = self.client.get("/api/students")
                self.assertEqual(response.status_code, 200)
                mock_list_students.assert_called_once()


    def test_migration_cli_parser(self):
        """Verify the migration script argument parser works properly."""
        from scripts.migrate_to_auradb import parse_args
        with patch("sys.argv", ["migrate_to_auradb.py", "--uri", "neo4j+s://test.databases.neo4j.io", "--dry-run"]):
            args = parse_args()
            self.assertEqual(args.uri, "neo4j+s://test.databases.neo4j.io")
            self.assertTrue(args.dry_run)
            self.assertFalse(args.clear_first)


if __name__ == "__main__":
    unittest.main()
