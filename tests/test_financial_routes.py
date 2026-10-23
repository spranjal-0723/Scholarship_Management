"""Unit tests for Flask financial routes in neo4j_routes.py."""

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


class FinancialRoutesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(neo4j_bp)
        self.client = self.app.test_client()

    # ---------------------------------------------------------
    # Dashboard Endpoint
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.get_dashboard_summary")
    def test_get_dashboard_route_success(self, mock_dash):
        mock_dash.return_value = {
            "total_students": 5,
            "total_scholarships": 5,
            "total_scholarship_amount": 180000.0,
            "total_fees": 380000.0,
            "total_paid": 100000.0,
            "total_outstanding": 280000.0,
            "pending_applications": 1,
            "approved_applications": 3,
        }
        res = self.client.get("/api/neo4j/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["total_students"], 5)
        self.assertEqual(data["total_outstanding"], 280000.0)

    @patch("backend.neo4j_routes.get_dashboard_summary")
    def test_get_dashboard_route_neo4j_error(self, mock_dash):
        mock_dash.side_effect = Neo4jError("Connection failed")
        res = self.client.get("/api/neo4j/dashboard")
        self.assertEqual(res.status_code, 503)

    # ---------------------------------------------------------
    # Fees Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_fees")
    def test_list_fees_route_success(self, mock_list):
        mock_list.return_value = [{"feeId": "F001", "feeAmount": 75000.0}]
        res = self.client.get("/api/neo4j/fees?limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["fees"][0]["feeId"], "F001")

    @patch("backend.neo4j_routes.list_fees")
    def test_list_fees_route_invalid_limit(self, mock_list):
        mock_list.side_effect = service.InvalidInputError("Invalid limit")
        res = self.client.get("/api/neo4j/fees?limit=invalid")
        self.assertEqual(res.status_code, 400)

    @patch("backend.neo4j_routes.get_fee")
    def test_get_fee_route_success(self, mock_get):
        mock_get.return_value = {"feeId": "F001", "feeAmount": 75000.0}
        res = self.client.get("/api/neo4j/fees/F001")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["fee"]["feeId"], "F001")

    @patch("backend.neo4j_routes.get_fee")
    def test_get_fee_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Fee not found")
        res = self.client.get("/api/neo4j/fees/F999")
        self.assertEqual(res.status_code, 404)

    @patch("backend.neo4j_routes.create_fee")
    def test_create_fee_route_success(self, mock_create):
        mock_create.return_value = {
            "feeId": "F006",
            "studentId": "S001",
            "feeAmount": 50000.0,
            "dueDate": "2026-04-01",
        }
        res = self.client.post("/api/neo4j/fees", json={
            "fee_id": "F006",
            "student_id": "S001",
            "fee_amount": 50000,
            "due_date": "2026-04-01",
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["fee_id"], "F006")
        self.assertEqual(data["fee_amount"], 50000.0)

    @patch("backend.neo4j_routes.create_fee")
    def test_create_fee_route_conflict(self, mock_create):
        mock_create.side_effect = service.ConflictError("Fee exists")
        res = self.client.post("/api/neo4j/fees", json={"fee_id": "F001"})
        self.assertEqual(res.status_code, 409)

    def test_create_fee_route_invalid_json(self):
        res = self.client.post("/api/neo4j/fees", data="invalid non-json")
        self.assertEqual(res.status_code, 400)

    @patch("backend.neo4j_routes.get_student_fees")
    def test_get_student_fees_route_success(self, mock_get):
        mock_get.return_value = [{"feeId": "F001", "studentId": "S001"}]
        res = self.client.get("/api/neo4j/students/S001/fees")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_student_fees")
    def test_get_student_fees_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Student not found")
        res = self.client.get("/api/neo4j/students/S999/fees")
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # Payments Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_payments")
    def test_list_payments_route_success(self, mock_list):
        mock_list.return_value = [{"paymentId": "PAY001", "amountPaid": 25000.0}]
        res = self.client.get("/api/neo4j/payments")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_payment")
    def test_get_payment_route_success(self, mock_get):
        mock_get.return_value = {"paymentId": "PAY001", "amountPaid": 25000.0}
        res = self.client.get("/api/neo4j/payments/PAY001")
        self.assertEqual(res.status_code, 200)

    @patch("backend.neo4j_routes.get_payment")
    def test_get_payment_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Payment not found")
        res = self.client.get("/api/neo4j/payments/PAY999")
        self.assertEqual(res.status_code, 404)

    @patch("backend.neo4j_routes.create_payment")
    def test_create_payment_route_success(self, mock_create):
        mock_create.return_value = {
            "paymentId": "PAY100",
            "transactionId": "TXN100",
            "amountPaid": 5000.0,
        }
        res = self.client.post("/api/neo4j/payments", json={
            "payment_id": "PAY100",
            "fee_id": "F001",
            "method_id": "M01",
            "payment_date": "2026-03-01",
            "amount_paid": 5000,
            "transaction_id": "TXN100",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["payment_id"], "PAY100")

    @patch("backend.neo4j_routes.create_payment")
    def test_create_payment_route_conflict(self, mock_create):
        mock_create.side_effect = service.ConflictError("Duplicate payment")
        res = self.client.post("/api/neo4j/payments", json={"payment_id": "PAY001"})
        self.assertEqual(res.status_code, 409)

    @patch("backend.neo4j_routes.get_student_payments")
    def test_get_student_payments_route_success(self, mock_get):
        mock_get.return_value = [{"paymentId": "PAY001"}]
        res = self.client.get("/api/neo4j/students/S001/payments")
        self.assertEqual(res.status_code, 200)

    # ---------------------------------------------------------
    # Disbursements Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_disbursements")
    def test_list_disbursements_route_success(self, mock_list):
        mock_list.return_value = [{"disbursementId": "DIS001", "amount": 50000.0}]
        res = self.client.get("/api/neo4j/disbursements")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_disbursement")
    def test_get_disbursement_route_success(self, mock_get):
        mock_get.return_value = {"disbursementId": "DIS001"}
        res = self.client.get("/api/neo4j/disbursements/DIS001")
        self.assertEqual(res.status_code, 200)

    @patch("backend.neo4j_routes.create_disbursement")
    def test_create_disbursement_route_success(self, mock_create):
        mock_create.return_value = {
            "disbursementId": "DIS100",
            "amount": 10000.0,
        }
        res = self.client.post("/api/neo4j/disbursements", json={
            "disbursement_id": "DIS100",
            "scholarship_id": "SCH001",
            "account_no": "AC001",
            "disbursement_date": "2026-03-01",
            "amount": 10000,
            "disbursement_mode": "Bank Transfer",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["disbursement_id"], "DIS100")

    @patch("backend.neo4j_routes.create_disbursement")
    def test_create_disbursement_route_invalid_input(self, mock_create):
        mock_create.side_effect = service.InvalidInputError("Invalid mode")
        res = self.client.post("/api/neo4j/disbursements", json={"disbursement_id": "DIS100"})
        self.assertEqual(res.status_code, 400)

    # ---------------------------------------------------------
    # Bank Accounts Endpoints
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.list_bank_accounts")
    def test_list_bank_accounts_route_success(self, mock_list):
        mock_list.return_value = [{"accountNo": "AC001", "bankName": "SBI"}]
        res = self.client.get("/api/neo4j/bank-accounts")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_bank_account")
    def test_get_bank_account_route_success(self, mock_get):
        mock_get.return_value = {"accountNo": "AC001", "bankName": "SBI"}
        res = self.client.get("/api/neo4j/bank-accounts/AC001")
        self.assertEqual(res.status_code, 200)

    @patch("backend.neo4j_routes.create_bank_account")
    def test_create_bank_account_route_success(self, mock_create):
        mock_create.return_value = {"accountNo": "AC100", "bankName": "Kotak"}
        res = self.client.post("/api/neo4j/bank-accounts", json={
            "account_no": "AC100",
            "bank_name": "Kotak",
            "ifsc": "KKBK0001",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["account_no"], "AC100")

    # ---------------------------------------------------------
    # Student Scholarships Endpoint
    # ---------------------------------------------------------
    @patch("backend.neo4j_routes.get_student_scholarships")
    def test_get_student_scholarships_route_success(self, mock_get):
        mock_get.return_value = [{"scholarshipId": "SCH001", "studentId": "S001"}]
        res = self.client.get("/api/neo4j/students/S001/scholarships")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

    @patch("backend.neo4j_routes.get_student_scholarships")
    def test_get_student_scholarships_route_not_found(self, mock_get):
        mock_get.side_effect = service.NotFoundError("Student not found")
        res = self.client.get("/api/neo4j/students/S999/scholarships")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
