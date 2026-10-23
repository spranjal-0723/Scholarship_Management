"""
Regression and validation test suite for server-side authentication,
CSRF verification, rate limiting, graph presets, system diagnostics,
and realistic demo dataset integrity.
"""

import unittest
from backend.app import app
from backend.auth import (
    DEMO_EMAIL,
    _DEFAULT_DEMO_PASSWORD,
    _clear_failed_attempts,
    _FAILED_LOGIN_ATTEMPTS
)


class TestAuthenticationAndRefinements(unittest.TestCase):
    """Test suite verifying Phase 1-7 refinements without regressing core APIs."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        _clear_failed_attempts("127.0.0.1")

    def tearDown(self):
        _clear_failed_attempts("127.0.0.1")

    # ============================================================
    # 1. AUTHENTICATION & SESSION TESTS
    # ============================================================

    def test_login_success_with_demo_credentials(self):
        """Verify demo administrator can authenticate and receive session + CSRF token."""
        response = self.client.post("/api/auth/login", json={
            "email": DEMO_EMAIL,
            "password": _DEFAULT_DEMO_PASSWORD
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], DEMO_EMAIL)
        self.assertEqual(data["user"]["role"], "Administrator")
        self.assertIn("csrf_token", data)
        self.assertTrue(len(data["csrf_token"]) >= 32)

    def test_login_invalid_password_returns_401(self):
        """Verify invalid credentials return 401 Unauthorized."""
        response = self.client.post("/api/auth/login", json={
            "email": DEMO_EMAIL,
            "password": "WrongPassword123!"
        })
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid", data["error"])

    def test_login_missing_fields_returns_400(self):
        """Verify missing email or password returns 400 Bad Request."""
        response = self.client.post("/api/auth/login", json={
            "email": DEMO_EMAIL
        })
        self.assertEqual(response.status_code, 400)

    def test_login_rate_limiting(self):
        """Verify that 5 failed attempts triggers HTTP 429 rate limit."""
        # 5 failed attempts
        for i in range(5):
            res = self.client.post("/api/auth/login", json={
                "email": DEMO_EMAIL,
                "password": f"BadPassword{i}"
            })
            self.assertEqual(res.status_code, 401)

        # 6th attempt should be blocked by rate limiting
        res6 = self.client.post("/api/auth/login", json={
            "email": DEMO_EMAIL,
            "password": "BadPassword6"
        })
        self.assertEqual(res6.status_code, 429)
        data = res6.get_json()
        self.assertIn("Too many failed login attempts", data["error"])

    def test_auth_me_authenticated_and_logout(self):
        """Verify /api/auth/me returns active user and logout terminates session."""
        # Step 1: Unauthenticated me
        res0 = self.client.get("/api/auth/me")
        self.assertEqual(res0.status_code, 401)

        # Step 2: Login
        login_res = self.client.post("/api/auth/login", json={
            "email": DEMO_EMAIL,
            "password": _DEFAULT_DEMO_PASSWORD
        })
        self.assertEqual(login_res.status_code, 200)

        # Step 3: Authenticated me
        res1 = self.client.get("/api/auth/me")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertTrue(data1["authenticated"])
        self.assertEqual(data1["user"]["email"], DEMO_EMAIL)

        # Step 4: Logout
        logout_res = self.client.post("/api/auth/logout")
        self.assertEqual(logout_res.status_code, 200)

        # Step 5: Post-logout me
        res2 = self.client.get("/api/auth/me")
        self.assertEqual(res2.status_code, 401)

    # ============================================================
    # 2. CSRF VERIFICATION TESTS
    # ============================================================

    def test_csrf_token_endpoint(self):
        """Verify /api/auth/csrf generates or returns a session token."""
        res = self.client.get("/api/auth/csrf")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("csrf_token", data)
        self.assertTrue(len(data["csrf_token"]) >= 32)

    # ============================================================
    # 3. NEO4J GRAPH PRESET TESTS
    # ============================================================

    def test_graph_preset_student_journey(self):
        """Verify student_journey preset returns nodes and edges."""
        res = self.client.get("/api/neo4j/graph?preset=student_journey")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)
        self.assertGreater(len(data["edges"]), 0)

    def test_graph_preset_scholarship_lifecycle(self):
        """Verify scholarship_lifecycle preset returns expected graph data."""
        res = self.client.get("/api/neo4j/graph?preset=scholarship_lifecycle")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    def test_graph_preset_fee_payment_flow(self):
        """Verify fee_payment_flow preset returns expected graph data."""
        res = self.client.get("/api/neo4j/graph?preset=fee_payment_flow")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    def test_graph_preset_department_network(self):
        """Verify department_network preset returns expected graph data."""
        res = self.client.get("/api/neo4j/graph?preset=department_network")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    def test_graph_preset_complete(self):
        """Verify complete preset returns full graph topology."""
        res = self.client.get("/api/neo4j/graph?preset=complete&limit=100")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    # ============================================================
    # 4. SYSTEM HEALTH & DIAGNOSTICS TESTS
    # ============================================================

    def test_system_health_endpoint(self):
        """Verify /api/health returns consolidated component status and counts."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("flask", data)
        self.assertEqual(data["flask"]["status"], "healthy")
        self.assertIn("oracle", data)
        self.assertEqual(data["oracle"]["status"], "connected")
        self.assertEqual(data["oracle"]["tables"], 12)
        self.assertGreaterEqual(data["oracle"]["total_records"], 200)
        self.assertIn("neo4j", data)
        self.assertEqual(data["neo4j"]["status"], "connected")
        self.assertGreaterEqual(data["neo4j"]["total_nodes"], 200)
        self.assertGreaterEqual(data["neo4j"]["total_edges"], 200)


if __name__ == "__main__":
    unittest.main()
