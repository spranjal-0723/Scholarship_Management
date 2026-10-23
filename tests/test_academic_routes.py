"""Unit tests for Flask academic routes in neo4j_routes.py."""

import unittest
from unittest.mock import patch
from flask import Flask
from neo4j.exceptions import Neo4jError

try:
    from backend.neo4j_routes import neo4j_bp
    from backend import graph_service as service
except ModuleNotFoundError:
    from neo4j_routes import neo4j_bp
    import graph_service as service


class AcademicRoutesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(neo4j_bp)
        self.client = self.app.test_client()

    # ---------------------------------------------------------
    # Students Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_students")
    def test_list_students_route_success(self, mock_list):
        mock_list.return_value = [{"studentId": "S001", "studentName": "Aarav"}]
        res = self.client.get("/api/neo4j/students?limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["students"][0]["studentId"], "S001")

    @patch("backend.neo4j_routes.list_students")
    def test_list_students_route_invalid_limit(self, mock_list):
        mock_list.side_effect = service.InvalidInputError("Limit error")
        res = self.client.get("/api/neo4j/students?limit=invalid")
        self.assertEqual(res.status_code, 400)

    @patch("backend.neo4j_routes.get_student")
    def test_get_student_route_success(self, mock_get):
        mock_get.return_value = {"studentId": "S001", "studentName": "Aarav"}
        res = self.client.get("/api/neo4j/students/S001")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["student"]["studentId"], "S001")

    @patch("backend.neo4j_routes.get_student")
    def test_get_student_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Student not found")
        res = self.client.get("/api/neo4j/students/S999")
        self.assertEqual(res.status_code, 404)

    @patch("backend.neo4j_routes.create_student")
    def test_create_student_route_success(self, mock_create):
        payload = {"studentId": "S100", "studentName": "Alice", "phone": "12345"}
        mock_create.return_value = payload
        res = self.client.post("/api/neo4j/students", json=payload)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["student"]["studentId"], "S100")

    def test_create_student_route_invalid_json(self):
        res = self.client.post("/api/neo4j/students", data="not json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

    @patch("backend.neo4j_routes.create_student")
    def test_create_student_route_duplicate(self, mock_create):
        mock_create.side_effect = service.ConflictError("Duplicate")
        res = self.client.post("/api/neo4j/students", json={"studentId": "S001", "studentName": "Aarav", "phone": "123"})
        self.assertEqual(res.status_code, 409)

    @patch("backend.neo4j_routes.get_student_profile")
    def test_get_student_profile_route_success(self, mock_get):
        mock_get.return_value = {"studentId": "S001", "bloodGroup": "O+"}
        res = self.client.get("/api/neo4j/students/S001/profile")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["profile"]["bloodGroup"], "O+")

    @patch("backend.neo4j_routes.get_student_profile")
    def test_get_student_profile_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Not found")
        res = self.client.get("/api/neo4j/students/S001/profile")
        self.assertEqual(res.status_code, 404)

    @patch("backend.neo4j_routes.get_student_guardians")
    def test_get_student_guardians_route_success(self, mock_get):
        mock_get.return_value = [{"guardianId": "G001", "guardianName": "Ramesh"}]
        res = self.client.get("/api/neo4j/students/S001/guardians")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["count"], 1)

    # ---------------------------------------------------------
    # Departments & Programs Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_departments")
    def test_list_departments_route(self, mock_list):
        mock_list.return_value = [{"deptId": "D01", "deptName": "CS"}]
        res = self.client.get("/api/neo4j/departments")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_department")
    def test_get_department_route(self, mock_get):
        mock_get.return_value = {
            "department": {"deptId": "D01", "deptName": "CS"},
            "programs": [{"programId": "P01"}],
        }
        res = self.client.get("/api/neo4j/departments/D01")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()["programs"]), 1)

    @patch("backend.neo4j_routes.get_department")
    def test_get_department_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Not found")
        res = self.client.get("/api/neo4j/departments/D99")
        self.assertEqual(res.status_code, 404)

    @patch("backend.neo4j_routes.list_programs")
    def test_list_programs_route(self, mock_list):
        mock_list.return_value = [{"programId": "P01", "programName": "CSE"}]
        res = self.client.get("/api/neo4j/programs")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_program_students")
    def test_get_program_students_route(self, mock_get):
        mock_get.return_value = {
            "programId": "P01",
            "students": [{"studentId": "S001"}],
            "count": 1,
        }
        res = self.client.get("/api/neo4j/programs/P01/students")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    # ---------------------------------------------------------
    # Applications Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_applications")
    def test_list_applications_route(self, mock_list):
        mock_list.return_value = [{"applicationId": "APP001", "applicationStatus": "Approved"}]
        res = self.client.get("/api/neo4j/applications?status=Approved")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_application")
    def test_get_application_route(self, mock_get):
        mock_get.return_value = {
            "application": {"applicationId": "APP001"},
            "student": {"studentId": "S001"},
            "scholarship": None,
        }
        res = self.client.get("/api/neo4j/applications/APP001")
        self.assertEqual(res.status_code, 200)

    @patch("backend.neo4j_routes.create_application")
    def test_create_application_route(self, mock_create):
        payload = {"applicationId": "APP100", "studentId": "S001"}
        mock_create.return_value = payload
        res = self.client.post("/api/neo4j/applications", json=payload)
        self.assertEqual(res.status_code, 201)

    @patch("backend.neo4j_routes.update_application_status")
    def test_update_application_status_route(self, mock_update):
        mock_update.return_value = {"applicationId": "APP001", "applicationStatus": "Approved"}
        res = self.client.put("/api/neo4j/applications/APP001/status", json={"status": "Approved"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["application"]["applicationStatus"], "Approved")

    def test_update_application_status_missing_status_body(self):
        res = self.client.put("/api/neo4j/applications/APP001/status", json={})
        self.assertEqual(res.status_code, 400)

    @patch("backend.neo4j_routes.get_student_applications")
    def test_get_student_applications_route(self, mock_get):
        mock_get.return_value = [{"applicationId": "APP001"}]
        res = self.client.get("/api/neo4j/students/S001/applications")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    # ---------------------------------------------------------
    # Scholarships Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_scholarships")
    def test_list_scholarships_route(self, mock_list):
        mock_list.return_value = [{"scholarshipId": "SCH001", "amount": 50000.0}]
        res = self.client.get("/api/neo4j/scholarships")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_scholarship")
    def test_get_scholarship_route(self, mock_get):
        mock_get.return_value = {
            "scholarship": {"scholarshipId": "SCH001", "amount": 50000.0},
            "application": {"applicationId": "APP001"},
            "student": {"studentId": "S001"},
            "disbursements": [],
        }
        res = self.client.get("/api/neo4j/scholarships/SCH001")
        self.assertEqual(res.status_code, 200)

    @patch("backend.neo4j_routes.create_scholarship")
    def test_create_scholarship_route(self, mock_create):
        payload = {
            "scholarshipId": "SCH100",
            "applicationId": "APP001",
            "scholarshipType": "Merit",
            "amount": 50000,
        }
        mock_create.return_value = payload
        res = self.client.post("/api/neo4j/scholarships", json=payload)
        self.assertEqual(res.status_code, 201)

    @patch("backend.neo4j_routes.create_scholarship")
    def test_create_scholarship_route_conflict(self, mock_create):
        mock_create.side_effect = service.ConflictError("Scholarships can only be awarded to approved applications.")
        payload = {
            "scholarshipId": "SCH100",
            "applicationId": "APP002",
            "scholarshipType": "Merit",
            "amount": 30000,
        }
        res = self.client.post("/api/neo4j/scholarships", json=payload)
        self.assertEqual(res.status_code, 409)


if __name__ == "__main__":
    unittest.main()
