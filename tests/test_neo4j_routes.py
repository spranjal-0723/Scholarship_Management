"""Unit tests for Neo4j Flask blueprint routes."""

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


class Neo4jRoutesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(neo4j_bp)
        self.client = self.app.test_client()

    # ---------------------------------------------------------
    # Health Endpoint (/api/neo4j/health)
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.verify_connection")
    def test_health_healthy(self, mock_verify):
        mock_verify.return_value = True
        response = self.client.get("/api/neo4j/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"database": "neo4j", "status": "ok"})

    @patch("backend.neo4j_routes.verify_connection")
    def test_health_unavailable_runtime_error(self, mock_verify):
        mock_verify.side_effect = RuntimeError("Connection failed")
        response = self.client.get("/api/neo4j/health")
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data, {"database": "neo4j", "status": "unavailable"})

    @patch("backend.neo4j_routes.verify_connection")
    def test_health_unavailable_neo4j_error(self, mock_verify):
        mock_verify.side_effect = Neo4jError("Server unreachable")
        response = self.client.get("/api/neo4j/health")
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["status"], "unavailable")

    # ---------------------------------------------------------
    # List Nodes Endpoint (GET /api/neo4j/nodes/<label>)
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_nodes")
    def test_list_nodes_success(self, mock_list):
        mock_list.return_value = [
            {"studentId": "S001", "studentName": "Alice"},
            {"studentId": "S002", "studentName": "Bob"},
        ]
        response = self.client.get("/api/neo4j/nodes/Student")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["items"]), 2)
        mock_list.assert_called_once_with("Student", limit=100)

    @patch("backend.neo4j_routes.list_nodes")
    def test_list_nodes_with_custom_limit(self, mock_list):
        mock_list.return_value = [{"studentId": "S001"}]
        response = self.client.get("/api/neo4j/nodes/Student?limit=25")
        self.assertEqual(response.status_code, 200)
        mock_list.assert_called_once_with("Student", limit=25)

    def test_list_nodes_invalid_limit_non_integer(self):
        response = self.client.get("/api/neo4j/nodes/Student?limit=abc")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    @patch("backend.neo4j_routes.list_nodes")
    def test_list_nodes_invalid_label(self, mock_list):
        mock_list.side_effect = service.InvalidInputError("Unsupported graph node label.")
        response = self.client.get("/api/neo4j/nodes/InvalidLabel")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid label or limit.")

    @patch("backend.neo4j_routes.list_nodes")
    def test_list_nodes_neo4j_error(self, mock_list):
        mock_list.side_effect = Neo4jError("Query timeout")
        response = self.client.get("/api/neo4j/nodes/Student")
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["error"], "Neo4j query failed.")

    @patch("backend.neo4j_routes.list_nodes")
    def test_list_nodes_generic_graph_service_error(self, mock_list):
        mock_list.side_effect = service.GraphServiceError("Internal failure")
        response = self.client.get("/api/neo4j/nodes/Student")
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data["error"], "Unable to retrieve graph nodes.")

    # ---------------------------------------------------------
    # Get Node Endpoint (GET /api/neo4j/nodes/<label>/<identifier>)
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.get_node")
    def test_get_node_success(self, mock_get):
        mock_get.return_value = {"studentId": "S001", "studentName": "Alice"}
        response = self.client.get("/api/neo4j/nodes/Student/S001")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["item"]["studentId"], "S001")
        mock_get.assert_called_once_with("Student", "S001")

    @patch("backend.neo4j_routes.get_node")
    def test_get_node_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Student was not found.")
        response = self.client.get("/api/neo4j/nodes/Student/S999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["error"], "Node not found.")

    @patch("backend.neo4j_routes.get_node")
    def test_get_node_invalid_input(self, mock_get):
        mock_get.side_effect = service.InvalidInputError("Invalid input")
        response = self.client.get("/api/neo4j/nodes/Unknown/S001")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid label or identifier.")

    @patch("backend.neo4j_routes.get_node")
    def test_get_node_neo4j_error(self, mock_get):
        mock_get.side_effect = Neo4jError("Neo4j down")
        response = self.client.get("/api/neo4j/nodes/Student/S001")
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["error"], "Neo4j query failed.")

    @patch("backend.neo4j_routes.get_node")
    def test_get_node_graph_service_error(self, mock_get):
        mock_get.side_effect = service.GraphServiceError("Server error")
        response = self.client.get("/api/neo4j/nodes/Student/S001")
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data["error"], "Unable to retrieve graph node.")

    # ---------------------------------------------------------
    # Create Node Endpoint (POST /api/neo4j/nodes/<label>)
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.create_node")
    def test_create_node_success(self, mock_create):
        payload = {"studentId": "S001", "studentName": "Alice"}
        mock_create.return_value = payload
        response = self.client.post("/api/neo4j/nodes/Student", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["item"], payload)
        mock_create.assert_called_once_with("Student", payload)

    def test_create_node_rejects_non_json_body(self):
        response = self.client.post(
            "/api/neo4j/nodes/Student",
            data="not a json string",
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Request body must be a JSON object.")

    def test_create_node_rejects_json_list(self):
        response = self.client.post(
            "/api/neo4j/nodes/Student",
            json=[{"studentId": "S001"}],
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Request body must be a JSON object.")

    @patch("backend.neo4j_routes.create_node")
    def test_create_node_invalid_input(self, mock_create):
        mock_create.side_effect = service.InvalidInputError("Missing identifier")
        response = self.client.post(
            "/api/neo4j/nodes/Student",
            json={"studentName": "Bob"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid label, identifier, or properties.")

    @patch("backend.neo4j_routes.create_node")
    def test_create_node_conflict_duplicate(self, mock_create):
        mock_create.side_effect = service.ConflictError("Duplicate")
        response = self.client.post(
            "/api/neo4j/nodes/Student",
            json={"studentId": "S001", "studentName": "Alice"},
        )
        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        self.assertEqual(data["error"], "Node with this identifier already exists.")

    @patch("backend.neo4j_routes.create_node")
    def test_create_node_neo4j_error(self, mock_create):
        mock_create.side_effect = Neo4jError("Session expired")
        response = self.client.post(
            "/api/neo4j/nodes/Student",
            json={"studentId": "S001"},
        )
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["error"], "Neo4j query failed.")

    @patch("backend.neo4j_routes.create_node")
    def test_create_node_graph_service_error(self, mock_create):
        mock_create.side_effect = service.GraphServiceError("Creation error")
        response = self.client.post(
            "/api/neo4j/nodes/Student",
            json={"studentId": "S001"},
        )
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data["error"], "Unable to create graph node.")

    def test_create_node_route_rejects_unknown_property(self):
        response = self.client.post(
            "/api/neo4j/nodes/Department",
            json={"deptId": "D01", "deptName": "CS", "extraField": "bad"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid label, identifier, or properties.")

    def test_create_node_route_rejects_nested_dict(self):
        response = self.client.post(
            "/api/neo4j/nodes/Department",
            json={"deptId": "D01", "deptName": {"en": "CS"}},
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid label, identifier, or properties.")

    def test_create_node_route_rejects_heterogeneous_array(self):
        response = self.client.post(
            "/api/neo4j/nodes/Department",
            json={"deptId": "D01", "deptName": [1, "two"]},
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid label, identifier, or properties.")

    # ---------------------------------------------------------
    # Graph Visualization Endpoint (GET /api/neo4j/graph)
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.get_graph_data")
    def test_get_graph_route_success(self, mock_graph):
        mock_graph.return_value = {
            "nodes": [{"data": {"id": "1", "label": "Student"}}],
            "edges": [],
            "total_nodes": 1,
            "total_edges": 0,
        }
        response = self.client.get("/api/neo4j/graph")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total_nodes"], 1)
        self.assertEqual(len(data["nodes"]), 1)

    @patch("backend.neo4j_routes.get_graph_data")
    def test_get_graph_route_invalid_label(self, mock_graph):
        mock_graph.side_effect = service.InvalidInputError("Unsupported label filter 'BadLabel'.")
        response = self.client.get("/api/neo4j/graph?label=BadLabel")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("Unsupported label", data["error"])

    @patch("backend.neo4j_routes.get_graph_data")
    def test_get_graph_route_student_not_found(self, mock_graph):
        mock_graph.side_effect = service.NotFoundError("Student 'UNKNOWN' was not found.")
        response = self.client.get("/api/neo4j/graph?student_id=UNKNOWN")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn("not found", data["error"])

    @patch("backend.neo4j_routes.get_graph_data")
    def test_get_graph_route_neo4j_error(self, mock_graph):
        mock_graph.side_effect = Neo4jError("Database offline")
        response = self.client.get("/api/neo4j/graph")
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["error"], "Neo4j query failed.")


if __name__ == "__main__":
    unittest.main()
