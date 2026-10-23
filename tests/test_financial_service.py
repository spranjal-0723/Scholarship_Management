"""Unit tests for financial graph services and business rules (DA-3)."""

import unittest
from unittest.mock import MagicMock, patch

from backend import graph_service as service


class FakeResult:
    def __init__(self, record=None, records=None):
        self._record = record
        self._records = records

    def single(self):
        if self._record is not None:
            return self._record
        if self._records:
            return self._records[0]
        return None

    def __iter__(self):
        if self._records is not None:
            return iter(self._records)
        return iter([] if self._record is None else [self._record])


class FinancialServiceTests(unittest.TestCase):
    # ---------------------------------------------------------
    # Fees
    # ---------------------------------------------------------
    def test_list_fees_success(self):
        fake_records = [
            {
                "feeId": "F001",
                "studentId": "S001",
                "studentName": "Aarav Sharma",
                "feeAmount": 75000.0,
                "dueDate": "2026-03-01",
                "amountPaid": 35000.0,
                "outstandingAmount": 40000.0,
            }
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            fees = service.list_fees(limit=10)

        self.assertEqual(len(fees), 1)
        self.assertEqual(fees[0]["feeId"], "F001")
        self.assertEqual(fees[0]["FEEID"], "F001")
        self.assertEqual(fees[0]["amountPaid"], 35000.0)
        self.assertEqual(fees[0]["outstandingAmount"], 40000.0)

    def test_list_fees_invalid_limit(self):
        with self.assertRaises(service.InvalidInputError):
            service.list_fees(limit="invalid")
        with self.assertRaises(service.InvalidInputError):
            service.list_fees(limit=-1)

    def test_get_fee_success(self):
        fake_rec = {
            "feeId": "F001",
            "studentId": "S001",
            "studentName": "Aarav Sharma",
            "feeAmount": 75000.0,
            "dueDate": "2026-03-01",
            "amountPaid": 25000.0,
            "outstandingAmount": 50000.0,
            "paymentsList": [
                {
                    "paymentId": "PAY001",
                    "feeId": "F001",
                    "studentId": "S001",
                    "studentName": "Aarav Sharma",
                    "scholarshipId": "SCH001",
                    "methodId": "M01",
                    "methodName": "UPI",
                    "paymentDate": "2026-02-25",
                    "amountPaid": 25000.0,
                    "transactionId": "TXN1001",
                }
            ],
        }
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            res = service.get_fee("F001")

        self.assertEqual(res["feeId"], "F001")
        self.assertEqual(len(res["payments"]), 1)
        self.assertEqual(res["payments"][0]["paymentId"], "PAY001")

    def test_get_fee_not_found(self):
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = None
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.get_fee("F999")

    def test_get_student_fees_success(self):
        mock_session = MagicMock()
        mock_session.run.side_effect = [
            FakeResult(record={"studentName": "Aarav Sharma"}),
            FakeResult(records=[
                {
                    "feeId": "F001",
                    "studentId": "S001",
                    "studentName": "Aarav Sharma",
                    "feeAmount": 75000.0,
                    "dueDate": "2026-03-01",
                    "amountPaid": 35000.0,
                    "outstandingAmount": 40000.0,
                }
            ]),
        ]
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            fees = service.get_student_fees("S001")

        self.assertEqual(len(fees), 1)
        self.assertEqual(fees[0]["studentId"], "S001")

    def test_get_student_fees_student_not_found(self):
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = None
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.get_student_fees("S999")

    def test_create_fee_missing_required_fields(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_fee({})
        with self.assertRaises(service.InvalidInputError):
            service.create_fee({"fee_id": "F100"})

    def test_create_fee_negative_amount(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_fee({
                "fee_id": "F100",
                "student_id": "S001",
                "fee_amount": -500,
                "due_date": "2026-04-01",
            })

    def test_create_fee_non_numeric_amount(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_fee({
                "fee_id": "F100",
                "student_id": "S001",
                "fee_amount": "invalid_number",
                "due_date": "2026-04-01",
            })

    def test_create_fee_duplicate_conflict(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.return_value.single.return_value = {"feeId": "F001"}
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.ConflictError):
                service.create_fee({
                    "fee_id": "F001",
                    "student_id": "S001",
                    "fee_amount": 50000,
                    "due_date": "2026-04-01",
                })

    def test_create_fee_student_not_found(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # fee duplicate check
                FakeResult(record=None),  # student exists check
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.create_fee({
                    "fee_id": "F999",
                    "student_id": "S999",
                    "fee_amount": 50000,
                    "due_date": "2026-04-01",
                })

    def test_create_fee_success(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # fee duplicate check
                FakeResult(record={"name": "Aarav Sharma"}),  # student exists
                FakeResult(record=None),  # create query
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            res = service.create_fee({
                "fee_id": "F006",
                "student_id": "S001",
                "fee_amount": 50000,
                "due_date": "2026-04-01",
            })

        self.assertEqual(res["feeId"], "F006")
        self.assertEqual(res["studentId"], "S001")
        self.assertEqual(res["feeAmount"], 50000.0)

    # ---------------------------------------------------------
    # Payments
    # ---------------------------------------------------------
    def test_list_payments_success(self):
        fake_records = [
            {
                "paymentId": "PAY001",
                "feeId": "F001",
                "studentId": "S001",
                "studentName": "Aarav Sharma",
                "scholarshipId": "SCH001",
                "methodId": "M01",
                "methodName": "UPI",
                "paymentDate": "2026-02-25",
                "amountPaid": 25000.0,
                "transactionId": "TXN1001",
            }
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            payments = service.list_payments(limit=10)

        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]["paymentId"], "PAY001")
        self.assertEqual(payments[0]["PAYMENTID"], "PAY001")
        self.assertEqual(payments[0]["amountPaid"], 25000.0)

    def test_create_payment_rejects_overpayment(self):
        """Verify Oracle PL/SQL TRG_CHECK_FEE_PAYMENT rule enforcement in Neo4j."""
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record={
                    "feeAmount": 75000.0,
                    "totalPaid": 70000.0,
                    "studentId": "S001",
                    "studentName": "Aarav",
                }),  # fee check
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.InvalidInputError) as ctx:
                service.create_payment({
                    "payment_id": "PAY999",
                    "fee_id": "F001",
                    "method_id": "M01",
                    "payment_date": "2026-03-01",
                    "amount_paid": 10000.0,  # 70000 + 10000 > 75000
                    "transaction_id": "TXN9999",
                })
            self.assertIn("Payment exceeds the total fee amount", str(ctx.exception))

    def test_create_payment_fee_not_found(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record=None),  # fee check
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.create_payment({
                    "payment_id": "PAY999",
                    "fee_id": "F999",
                    "method_id": "M01",
                    "payment_date": "2026-03-01",
                    "amount_paid": 5000.0,
                    "transaction_id": "TXN9999",
                })

    def test_create_payment_method_not_found(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record={
                    "feeAmount": 75000.0,
                    "totalPaid": 10000.0,
                    "studentId": "S001",
                    "studentName": "Aarav",
                }),  # fee check
                FakeResult(record=None),  # method check
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.create_payment({
                    "payment_id": "PAY999",
                    "fee_id": "F001",
                    "method_id": "M99",
                    "payment_date": "2026-03-01",
                    "amount_paid": 5000.0,
                    "transaction_id": "TXN9999",
                })

    def test_create_payment_success(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record={
                    "feeAmount": 75000.0,
                    "totalPaid": 20000.0,
                    "studentId": "S001",
                    "studentName": "Aarav",
                }),  # fee check
                FakeResult(record={"methodName": "UPI"}),  # method check
                FakeResult(record=None),  # create query
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            res = service.create_payment({
                "payment_id": "PAY100",
                "fee_id": "F001",
                "method_id": "M01",
                "payment_date": "2026-03-01",
                "amount_paid": 5000.0,
                "transaction_id": "TXN10001",
            })

        self.assertEqual(res["paymentId"], "PAY100")
        self.assertEqual(res["feeId"], "F001")
        self.assertEqual(res["amountPaid"], 5000.0)

    # ---------------------------------------------------------
    # Disbursements
    # ---------------------------------------------------------
    def test_list_disbursements_success(self):
        fake_records = [
            {
                "disbursementId": "DIS001",
                "scholarshipId": "SCH001",
                "applicationId": "APP001",
                "studentId": "S001",
                "studentName": "Aarav Sharma",
                "accountNo": "AC001",
                "bankName": "State Bank of India",
                "ifsc": "SBIN0001234",
                "disbursementDate": "2026-02-10",
                "amount": 50000.0,
                "disbursementMode": "Bank Transfer",
            }
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            disbursements = service.list_disbursements(limit=10)

        self.assertEqual(len(disbursements), 1)
        self.assertEqual(disbursements[0]["disbursementId"], "DIS001")
        self.assertEqual(disbursements[0]["DISBURSEMENTID"], "DIS001")
        self.assertEqual(disbursements[0]["amount"], 50000.0)

    def test_create_disbursement_invalid_mode(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_disbursement({
                "disbursement_id": "DIS100",
                "scholarship_id": "SCH001",
                "account_no": "AC001",
                "disbursement_date": "2026-03-01",
                "amount": 10000,
                "disbursement_mode": "Cash",  # Invalid mode
            })

    def test_create_disbursement_exceeds_scholarship(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record={
                    "scholarshipAmount": 50000.0,
                    "totalDisbursed": 45000.0,
                    "applicationId": "APP001",
                    "studentId": "S001",
                    "studentName": "Aarav",
                }),  # scholarship check
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.InvalidInputError):
                service.create_disbursement({
                    "disbursement_id": "DIS100",
                    "scholarship_id": "SCH001",
                    "account_no": "AC001",
                    "disbursement_date": "2026-03-01",
                    "amount": 10000,  # 45000 + 10000 > 50000
                    "disbursement_mode": "Bank Transfer",
                })

    def test_create_disbursement_bank_not_found(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record={
                    "scholarshipAmount": 50000.0,
                    "totalDisbursed": 0.0,
                    "applicationId": "APP001",
                    "studentId": "S001",
                    "studentName": "Aarav",
                }),  # scholarship check
                FakeResult(record=None),  # bank account check
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.create_disbursement({
                    "disbursement_id": "DIS100",
                    "scholarship_id": "SCH001",
                    "account_no": "AC999",
                    "disbursement_date": "2026-03-01",
                    "amount": 10000,
                    "disbursement_mode": "Bank Transfer",
                })

    def test_create_disbursement_success(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record={
                    "scholarshipAmount": 50000.0,
                    "totalDisbursed": 20000.0,
                    "applicationId": "APP001",
                    "studentId": "S001",
                    "studentName": "Aarav",
                }),  # scholarship check
                FakeResult(record={"bankName": "SBI", "ifsc": "SBIN0001"}),  # bank check
                FakeResult(record=None),  # create query
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            res = service.create_disbursement({
                "disbursement_id": "DIS100",
                "scholarship_id": "SCH001",
                "account_no": "AC001",
                "disbursement_date": "2026-03-01",
                "amount": 10000,
                "disbursement_mode": "Bank Transfer",
            })

        self.assertEqual(res["disbursementId"], "DIS100")
        self.assertEqual(res["amount"], 10000.0)

    # ---------------------------------------------------------
    # Bank Accounts
    # ---------------------------------------------------------
    def test_list_bank_accounts_success(self):
        fake_records = [
            {
                "accountNo": "AC001",
                "bankName": "State Bank of India",
                "ifsc": "SBIN0001234",
                "accountType": "Savings",
            }
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            accounts = service.list_bank_accounts(limit=10)

        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]["accountNo"], "AC001")
        self.assertEqual(accounts[0]["ACCOUNTNO"], "AC001")

    def test_create_bank_account_success(self):
        def fake_execute_write(fn):
            mock_tx = MagicMock()
            mock_tx.run.side_effect = [
                FakeResult(record=None),  # duplicate check
                FakeResult(record=None),  # create query
            ]
            return fn(mock_tx)

        mock_session = MagicMock()
        mock_session.execute_write.side_effect = fake_execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            res = service.create_bank_account({
                "account_no": "AC100",
                "bank_name": "Kotak Mahindra Bank",
                "ifsc": "KKBK0001234",
                "account_type": "Savings",
            })

        self.assertEqual(res["accountNo"], "AC100")
        self.assertEqual(res["bankName"], "Kotak Mahindra Bank")

    # ---------------------------------------------------------
    # Dashboard and Student Scholarships
    # ---------------------------------------------------------
    def test_get_dashboard_summary_success(self):
        fake_rec = {
            "total_students": 5,
            "total_scholarships": 5,
            "total_scholarship_amount": 180000.0,
            "total_fees": 380000.0,
            "total_paid": 100000.0,
            "total_outstanding": 280000.0,
            "pending_applications": 1,
            "approved_applications": 3,
        }
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            summary = service.get_dashboard_summary()

        self.assertEqual(summary["total_students"], 5)
        self.assertEqual(summary["total_scholarships"], 5)
        self.assertEqual(summary["total_scholarship_amount"], 180000.0)
        self.assertEqual(summary["total_fees"], 380000.0)
        self.assertEqual(summary["total_paid"], 100000.0)
        self.assertEqual(summary["total_outstanding"], 280000.0)

    def test_get_student_scholarships_success(self):
        mock_session = MagicMock()
        mock_session.run.side_effect = [
            FakeResult(record={"name": "Aarav Sharma"}),
            FakeResult(records=[
                {
                    "scholarshipId": "SCH001",
                    "studentId": "S001",
                    "studentName": "Aarav Sharma",
                    "scholarshipType": "Merit Scholarship",
                    "amount": 50000.0,
                    "applicationId": "APP001",
                    "applicationStatus": "Approved",
                }
            ]),
        ]
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            scholarships = service.get_student_scholarships("S001")

        self.assertEqual(len(scholarships), 1)
        self.assertEqual(scholarships[0]["scholarshipId"], "SCH001")
        self.assertEqual(scholarships[0]["SCHOLARSHIPID"], "SCH001")


if __name__ == "__main__":
    unittest.main()
