"""Safe live integration tests for Neo4j.

These tests run against the live Neo4j container if available.
They use isolated, uniquely identified test fixtures and clean up
strictly the records they create, leaving the shared database pristine.
"""

import unittest
import uuid

try:
    from backend import graph_service as service
    from backend import neo4j_db as db
except ModuleNotFoundError:
    import graph_service as service
    import neo4j_db as db


def is_neo4j_reachable():
    try:
        return db.verify_connection()
    except Exception:
        return False


NEO4J_AVAILABLE = is_neo4j_reachable()


@unittest.skipUnless(NEO4J_AVAILABLE, "Live Neo4j instance is not reachable")
class LiveNeo4jIntegrationTests(unittest.TestCase):
    def setUp(self):
        uid = uuid.uuid4().hex[:8].upper()
        self.test_student_id = f"TEST_S_{uid}"
        self.test_prog_id = f"TEST_P_{uid}"
        self.test_app_id = f"TEST_A_{uid}"
        self.test_sch_id = f"TEST_SCH_{uid}"
        self.test_fee_id = f"TEST_F_{uid}"
        self.test_pay_id = f"TEST_PAY_{uid}"
        self.test_txn_id = f"TEST_TXN_{uid}"
        self.test_ac_id = f"TEST_AC_{uid}"
        self.test_dis_id = f"TEST_DIS_{uid}"

    def tearDown(self):
        # Clean up only the records created during this test
        try:
            driver = db.get_driver()
            with driver.session(database=db.get_database_name()) as session:
                session.run(
                    """
                    MATCH (n)
                    WHERE n.studentId = $s_id
                       OR n.programId = $p_id
                       OR n.applicationId = $a_id
                       OR n.scholarshipId = $sch_id
                       OR n.feeId = $f_id
                       OR n.paymentId = $pay_id
                       OR n.accountNo = $ac_id
                       OR n.disbursementId = $dis_id
                    DETACH DELETE n
                    """,
                    s_id=self.test_student_id,
                    p_id=self.test_prog_id,
                    a_id=self.test_app_id,
                    sch_id=self.test_sch_id,
                    f_id=self.test_fee_id,
                    pay_id=self.test_pay_id,
                    ac_id=self.test_ac_id,
                    dis_id=self.test_dis_id,
                )
        except Exception:
            pass

    def test_live_verify_connection(self):
        """Verify connectivity to live Neo4j database."""
        self.assertTrue(db.verify_connection())

    def test_live_node_lifecycle_and_conflict(self):
        """Test create, retrieve, duplicate prevention, and deletion against live Neo4j."""
        driver = db.get_driver()

        # 1. Create a node with unique identifier
        created = service.create_node(
            "Student",
            {
                "studentId": self.test_student_id,
                "studentName": "Live Test Student",
                "phone": "9999999999",
            },
        )
        self.assertEqual(created["studentId"], self.test_student_id)
        self.assertEqual(created["studentName"], "Live Test Student")

        # 2. Retrieve the node
        retrieved = service.get_node("Student", self.test_student_id)
        self.assertEqual(retrieved["studentId"], self.test_student_id)
        self.assertEqual(retrieved["studentName"], "Live Test Student")

        # 3. Verify duplicate prevention raises ConflictError
        with self.assertRaises(service.ConflictError):
            service.create_node(
                "Student",
                {
                    "studentId": self.test_student_id,
                    "studentName": "Duplicate Student",
                },
            )

        # 4. Verify list_nodes includes our node
        items = service.list_nodes("Student", limit=50)
        found = any(item.get("studentId") == self.test_student_id for item in items)
        self.assertTrue(found)

        # 5. Clean up the node
        with driver.session(database=db.get_database_name()) as session:
            session.run(
                "MATCH (n:Student {studentId: $id}) DETACH DELETE n",
                id=self.test_student_id,
            )

        # 6. Verify node no longer exists
        with self.assertRaises(service.NotFoundError):
            service.get_node("Student", self.test_student_id)

    def test_live_academic_workflow_and_business_rules(self):
        """Test academic relationship workflow and business rules live against Neo4j."""
        driver = db.get_driver()

        # 1. Create a test program
        service.create_node(
            "Program",
            {
                "programId": self.test_prog_id,
                "programName": "Live Test Program",
                "degreeLevel": "BTech",
            },
        )

        # 2. Create student linked to program
        stu = service.create_student({
            "studentId": self.test_student_id,
            "studentName": "Live Academic Student",
            "phone": "9998887777",
            "programId": self.test_prog_id,
        })
        self.assertEqual(stu["studentId"], self.test_student_id)

        # 3. Retrieve student and verify program is populated
        detailed_stu = service.get_student(self.test_student_id)
        self.assertIn("program", detailed_stu)
        self.assertEqual(detailed_stu["program"]["programId"], self.test_prog_id)

        # 4. Create application for student (defaults to Pending)
        app = service.create_application({
            "applicationId": self.test_app_id,
            "studentId": self.test_student_id,
        })
        self.assertEqual(app["applicationStatus"], "Pending")

        # 5. Business Rule Check: Cannot create scholarship for a Pending application
        with self.assertRaises(service.ConflictError) as ctx:
            service.create_scholarship({
                "scholarshipId": self.test_sch_id,
                "applicationId": self.test_app_id,
                "scholarshipType": "Merit",
                "amount": 25000,
            })
        self.assertIn("approved", str(ctx.exception).lower())

        # 6. Update application status to Approved
        updated_app = service.update_application_status(self.test_app_id, "Approved")
        self.assertEqual(updated_app["applicationStatus"], "Approved")

        # 7. Create scholarship for Approved application
        sch = service.create_scholarship({
            "scholarshipId": self.test_sch_id,
            "applicationId": self.test_app_id,
            "scholarshipType": "Merit",
            "amount": 25000,
        })
        self.assertEqual(sch["scholarshipId"], self.test_sch_id)
        self.assertEqual(sch["amount"], 25000.0)

        # 8. Business Rule Check: Cannot create a second scholarship for same application (1:1 rule)
        second_sch_id = f"{self.test_sch_id}_2"
        with self.assertRaises(service.ConflictError) as ctx2:
            service.create_scholarship({
                "scholarshipId": second_sch_id,
                "applicationId": self.test_app_id,
                "scholarshipType": "Sports",
                "amount": 10000,
            })
        self.assertIn("already has an awarded scholarship", str(ctx2.exception))

        # 9. Verify get_scholarship returns linked application and student
        sch_details = service.get_scholarship(self.test_sch_id)
        self.assertEqual(sch_details["scholarship"]["scholarshipId"], self.test_sch_id)
        self.assertEqual(sch_details["application"]["applicationId"], self.test_app_id)
        self.assertEqual(sch_details["student"]["studentId"], self.test_student_id)

        # 10. Clean up all created test nodes
        with driver.session(database=db.get_database_name()) as session:
            session.run(
                """
                MATCH (n)
                WHERE n.studentId = $s_id
                   OR n.programId = $p_id
                   OR n.applicationId = $a_id
                   OR n.scholarshipId = $sch_id
                DETACH DELETE n
                """,
                s_id=self.test_student_id,
                p_id=self.test_prog_id,
                a_id=self.test_app_id,
                sch_id=self.test_sch_id,
            )

        # 11. Verify clean state
        with self.assertRaises(service.NotFoundError):
            service.get_student(self.test_student_id)

    def test_live_financial_workflow_and_business_rules(self):
        """Test financial lifecycle, payments, and overpayment prevention live against Neo4j."""
        driver = db.get_driver()

        # 1. Create a fee for existing student S001
        fee = service.create_fee({
            "fee_id": self.test_fee_id,
            "student_id": "S001",
            "fee_amount": 50000.0,
            "due_date": "2026-06-01",
        })
        self.assertEqual(fee["feeId"], self.test_fee_id)
        self.assertEqual(fee["feeAmount"], 50000.0)
        self.assertEqual(fee["outstandingAmount"], 50000.0)

        # 2. Record a partial payment of 20,000
        pay = service.create_payment({
            "payment_id": self.test_pay_id,
            "fee_id": self.test_fee_id,
            "method_id": "M01",
            "payment_date": "2026-05-15",
            "amount_paid": 20000.0,
            "transaction_id": self.test_txn_id,
        })
        self.assertEqual(pay["paymentId"], self.test_pay_id)
        self.assertEqual(pay["amountPaid"], 20000.0)

        # 3. Verify get_fee reflects updated balance
        updated_fee = service.get_fee(self.test_fee_id)
        self.assertEqual(updated_fee["amountPaid"], 20000.0)
        self.assertEqual(updated_fee["outstandingAmount"], 30000.0)
        self.assertEqual(len(updated_fee["payments"]), 1)

        # 4. Business Rule Check: Payment exceeding fee is rejected (TRG_CHECK_FEE_PAYMENT rule)
        # Remaining balance is 30,000; attempt to pay 35,000
        excess_pay_id = f"{self.test_pay_id}_EXCESS"
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_payment({
                "payment_id": excess_pay_id,
                "fee_id": self.test_fee_id,
                "method_id": "M01",
                "payment_date": "2026-05-20",
                "amount_paid": 35000.0,
                "transaction_id": f"TXN_{excess_pay_id}",
            })
        self.assertIn("exceeds the total fee amount", str(ctx.exception))

        # 5. Create a test bank account
        acc = service.create_bank_account({
            "account_no": self.test_ac_id,
            "bank_name": "Live Test Bank",
            "ifsc": "TEST0001234",
            "account_type": "Savings",
        })
        self.assertEqual(acc["accountNo"], self.test_ac_id)

        # 6. Verify dashboard summary runs against live graph and aggregates correctly
        summary = service.get_dashboard_summary()
        self.assertGreaterEqual(summary["total_students"], 5)
        self.assertGreaterEqual(summary["total_fees"], 380000.0)
        self.assertGreaterEqual(summary["total_paid"], 100000.0)

        # 7. Clean up all created test nodes
        with driver.session(database=db.get_database_name()) as session:
            session.run(
                """
                MATCH (n)
                WHERE n.studentId = $s_id
                   OR n.programId = $p_id
                   OR n.applicationId = $a_id
                   OR n.scholarshipId = $sch_id
                   OR n.feeId = $f_id
                   OR n.paymentId = $pay_id
                   OR n.accountNo = $ac_id
                   OR n.disbursementId = $dis_id
                DETACH DELETE n
                """,
                s_id=self.test_student_id,
                p_id=self.test_prog_id,
                a_id=self.test_app_id,
                sch_id=self.test_sch_id,
                f_id=self.test_fee_id,
                pay_id=self.test_pay_id,
                ac_id=self.test_ac_id,
                dis_id=self.test_dis_id,
            )

        # 8. Verify clean state
        with self.assertRaises(service.NotFoundError):
            service.get_fee(self.test_fee_id)


if __name__ == "__main__":
    unittest.main()
