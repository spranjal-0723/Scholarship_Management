"""Unit tests for academic graph services and business rules (Member 2)."""

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

    def data(self):
        if self._records is not None:
            return self._records
        if self._record is not None:
            return [self._record]
        return []

    def __iter__(self):
        if self._records is not None:
            return iter(self._records)
        return iter([] if self._record is None else [self._record])


class AcademicServiceTests(unittest.TestCase):
    # ---------------------------------------------------------
    # Students
    # ---------------------------------------------------------
    def test_list_students_success(self):
        fake_records = [
            {
                "student": {"studentId": "S001", "studentName": "Aarav"},
                "programName": "CSE",
                "degreeLevel": "BTech",
                "deptName": "CS",
            }
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            students = service.list_students(limit=10)

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["studentId"], "S001")
        self.assertEqual(students[0]["programName"], "CSE")

    def test_list_students_invalid_limit(self):
        with self.assertRaises(service.InvalidInputError):
            service.list_students(limit=0)
        with self.assertRaises(service.InvalidInputError):
            service.list_students(limit=600)
        with self.assertRaises(service.InvalidInputError):
            service.list_students(limit="100")

    def test_get_student_success(self):
        fake_rec = {
            "student": {"studentId": "S001", "studentName": "Aarav"},
            "program": {"programId": "P01", "programName": "CSE"},
            "department": {"deptId": "D01", "deptName": "CS"},
        }
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            student = service.get_student("S001")

        self.assertEqual(student["studentId"], "S001")
        self.assertEqual(student["program"]["programId"], "P01")
        self.assertEqual(student["department"]["deptId"], "D01")

    def test_get_student_not_found(self):
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = None
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError):
                service.get_student("S999")

    def test_create_student_rejects_unsupported_properties(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_student({
                "studentId": "S100",
                "studentName": "John",
                "phone": "1234567890",
                "unsupportedKey": "val",
            })
        self.assertIn("Unsupported property", str(ctx.exception))

    def test_create_student_missing_required_fields(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_student({"studentId": "S100"})
        with self.assertRaises(service.InvalidInputError):
            service.create_student({"studentId": "S100", "studentName": "John"})

    def test_create_student_success_with_program(self):
        mock_tx = MagicMock()
        # 1. existing check -> None
        # 2. program check -> found
        # 3. create -> item
        # 4. link
        mock_tx.run.side_effect = [
            FakeResult(None),  # student not exists
            FakeResult({"p": True}),  # program exists
            FakeResult({"item": {"studentId": "S100", "studentName": "John", "phone": "123", "programId": "P01"}}),
            FakeResult(None),  # link
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            created = service.create_student({
                "studentId": "S100",
                "studentName": "John",
                "phone": "123",
                "programId": "P01",
            })

        self.assertEqual(created["studentId"], "S100")
        self.assertEqual(created["programId"], "P01")

    def test_create_student_referenced_program_missing(self):
        mock_tx = MagicMock()
        mock_tx.run.side_effect = [
            FakeResult(None),  # student not exists
            FakeResult(None),  # program does NOT exist
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.InvalidInputError) as ctx:
                service.create_student({
                    "studentId": "S100",
                    "studentName": "John",
                    "phone": "123",
                    "programId": "P99",
                })
            self.assertIn("Referenced Program 'P99' does not exist", str(ctx.exception))

    def test_create_student_duplicate(self):
        mock_tx = MagicMock()
        mock_tx.run.return_value = FakeResult({"s": True})  # already exists
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.ConflictError):
                service.create_student({
                    "studentId": "S001",
                    "studentName": "John",
                    "phone": "123",
                })

    def test_get_student_profile_success(self):
        fake_rec = {"s": True, "profile": {"studentId": "S001", "bloodGroup": "O+"}}
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            profile = service.get_student_profile("S001")

        self.assertEqual(profile["bloodGroup"], "O+")

    def test_get_student_profile_missing_student(self):
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = None
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.NotFoundError) as ctx:
                service.get_student_profile("S999")
            self.assertIn("Student 'S999' was not found", str(ctx.exception))

    def test_get_student_guardians_success(self):
        fake_rec = {
            "s": True,
            "guardians": [{"guardianId": "G001", "guardianName": "Ramesh"}],
        }
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            guardians = service.get_student_guardians("S001")

        self.assertEqual(len(guardians), 1)
        self.assertEqual(guardians[0]["guardianId"], "G001")

    # ---------------------------------------------------------
    # Departments & Programs
    # ---------------------------------------------------------
    def test_list_departments(self):
        fake_records = [
            {"department": {"deptId": "D01", "deptName": "CS"}, "programCount": 1}
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            depts = service.list_departments()

        self.assertEqual(len(depts), 1)
        self.assertEqual(depts[0]["programCount"], 1)

    def test_get_department_success(self):
        fake_rec = {
            "department": {"deptId": "D01", "deptName": "CS"},
            "programs": [{"programId": "P01", "programName": "CSE"}],
        }
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            dept_data = service.get_department("D01")

        self.assertEqual(dept_data["department"]["deptId"], "D01")
        self.assertEqual(len(dept_data["programs"]), 1)

    def test_list_programs(self):
        fake_records = [
            {"program": {"programId": "P01", "programName": "CSE"}, "deptName": "CS"}
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            programs = service.list_programs()

        self.assertEqual(len(programs), 1)
        self.assertEqual(programs[0]["deptName"], "CS")

    def test_get_program_students_success(self):
        fake_rec = {
            "program": {"programId": "P01", "programName": "CSE"},
            "students": [{"studentId": "S001", "studentName": "Aarav"}],
        }
        mock_session = MagicMock()
        mock_session.run.return_value.single.return_value = fake_rec
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            data = service.get_program_students("P01")

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["students"][0]["studentId"], "S001")

    # ---------------------------------------------------------
    # Applications
    # ---------------------------------------------------------
    def test_list_applications_with_status_filter(self):
        fake_records = [
            {
                "application": {"applicationId": "APP001", "applicationStatus": "Approved"},
                "studentName": "Aarav",
                "scholarship": {"scholarshipId": "SCH001"},
            }
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = fake_records
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            apps = service.list_applications(status="Approved")

        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0]["applicationStatus"], "Approved")

    def test_list_applications_invalid_status_filter(self):
        with self.assertRaises(service.InvalidInputError):
            service.list_applications(status="InvalidStatus")

    def test_create_application_success(self):
        mock_tx = MagicMock()
        mock_tx.run.side_effect = [
            FakeResult({"s": True}),  # student exists
            FakeResult(None),  # app does not exist
            FakeResult({"item": {"applicationId": "APP100", "studentId": "S001", "applicationStatus": "Pending"}}),
            FakeResult(None),  # link
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            created = service.create_application({"applicationId": "APP100", "studentId": "S001"})

        self.assertEqual(created["applicationId"], "APP100")
        self.assertEqual(created["applicationStatus"], "Pending")

    def test_create_application_invalid_status(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_application({
                "applicationId": "APP100",
                "studentId": "S001",
                "applicationStatus": "UnknownStatus",
            })

    def test_create_application_referenced_student_missing(self):
        mock_tx = MagicMock()
        mock_tx.run.return_value = FakeResult(None)  # student missing
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.InvalidInputError) as ctx:
                service.create_application({"applicationId": "APP100", "studentId": "S999"})
            self.assertIn("Referenced Student 'S999' does not exist", str(ctx.exception))

    def test_update_application_status_success(self):
        mock_tx = MagicMock()
        mock_tx.run.return_value = FakeResult({"application": {"applicationId": "APP001", "applicationStatus": "Approved"}})
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            res = service.update_application_status("APP001", "Approved")

        self.assertEqual(res["applicationStatus"], "Approved")

    def test_update_application_status_invalid(self):
        with self.assertRaises(service.InvalidInputError):
            service.update_application_status("APP001", "NotAValidStatus")

    # ---------------------------------------------------------
    # Scholarships & Business Rules
    # ---------------------------------------------------------
    def test_create_scholarship_success_approved(self):
        mock_tx = MagicMock()
        mock_tx.run.side_effect = [
            FakeResult(None),  # scholarshipId doesn't exist
            FakeResult({"status": "Approved"}),  # application exists and Approved
            FakeResult(None),  # application does not already have a scholarship
            FakeResult({"item": {"scholarshipId": "SCH100", "applicationId": "APP001", "amount": 50000.0}}),
            FakeResult(None),  # link
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            created = service.create_scholarship({
                "scholarshipId": "SCH100",
                "applicationId": "APP001",
                "scholarshipType": "Merit",
                "amount": 50000,
            })

        self.assertEqual(created["scholarshipId"], "SCH100")
        self.assertEqual(created["amount"], 50000.0)

    def test_create_scholarship_rejects_pending_app(self):
        mock_tx = MagicMock()
        mock_tx.run.side_effect = [
            FakeResult(None),  # scholarshipId doesn't exist
            FakeResult({"status": "Pending"}),  # application is Pending!
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.ConflictError) as ctx:
                service.create_scholarship({
                    "scholarshipId": "SCH100",
                    "applicationId": "APP002",
                    "scholarshipType": "Merit",
                    "amount": 30000,
                })
            self.assertIn("Scholarships can only be awarded to approved applications", str(ctx.exception))

    def test_create_scholarship_rejects_rejected_app(self):
        mock_tx = MagicMock()
        mock_tx.run.side_effect = [
            FakeResult(None),  # scholarshipId doesn't exist
            FakeResult({"status": "Rejected"}),  # application is Rejected!
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.ConflictError) as ctx:
                service.create_scholarship({
                    "scholarshipId": "SCH100",
                    "applicationId": "APP004",
                    "scholarshipType": "Merit",
                    "amount": 25000,
                })
            self.assertIn("Scholarships can only be awarded to approved applications", str(ctx.exception))

    def test_create_scholarship_rejects_duplicate_award(self):
        mock_tx = MagicMock()
        mock_tx.run.side_effect = [
            FakeResult(None),  # scholarshipId doesn't exist
            FakeResult({"status": "Approved"}),  # application is Approved
            FakeResult({"s": True}),  # ALREADY has an awarded scholarship!
        ]
        mock_session = MagicMock()
        mock_session.execute_write.side_effect = lambda cb: cb(mock_tx)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        with patch.object(service, "get_driver", return_value=mock_driver):
            with self.assertRaises(service.ConflictError) as ctx:
                service.create_scholarship({
                    "scholarshipId": "SCH100",
                    "applicationId": "APP001",
                    "scholarshipType": "Merit",
                    "amount": 50000,
                })
            self.assertIn("already has an awarded scholarship", str(ctx.exception))

    def test_create_scholarship_rejects_negative_amount(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_scholarship({
                "scholarshipId": "SCH100",
                "applicationId": "APP001",
                "scholarshipType": "Merit",
                "amount": -500,
            })

    def test_create_scholarship_rejects_non_numeric_amount(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_scholarship({
                "scholarshipId": "SCH100",
                "applicationId": "APP001",
                "scholarshipType": "Merit",
                "amount": "fifty thousand",
            })


if __name__ == "__main__":
    unittest.main()
