import unittest
from unittest.mock import patch

from backend import graph_service as service


class FakeResult:
    def __init__(self, record=None, records=None):
        self.record = record
        self.records = records

    def single(self):
        if self.record is not None:
            return self.record
        if self.records:
            return self.records[0]
        return None

    def __iter__(self):
        if self.records is not None:
            return iter(self.records)
        return iter([] if self.record is None else [self.record])


class FakeTransaction:
    def __init__(self, existing=None, created=None):
        self.existing = existing
        self.created = created
        self.calls = []

    def run(self, query, **parameters):
        self.calls.append((query, parameters))

        if query.strip().startswith("MATCH (existing:"):
            return FakeResult(self.existing)

        return FakeResult({"item": self.created})


class FakeSession:
    def __init__(self, transaction=None, records=None):
        self.transaction = transaction or FakeTransaction()
        self.records = records or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def run(self, query, **parameters):
        self.last_query = query
        self.last_parameters = parameters

        if self.records:
            return FakeResult(records=self.records)

        return FakeResult()

    def execute_write(self, callback):
        return callback(self.transaction)


class FakeDriver:
    def __init__(self, session):
        self.fake_session = session

    def session(self, **kwargs):
        return self.fake_session


class GraphServiceTests(unittest.TestCase):
    def test_rejects_unknown_label(self):
        with self.assertRaises(service.InvalidInputError):
            service.list_nodes("UnknownLabel")

    def test_rejects_invalid_list_limit(self):
        with self.assertRaises(service.InvalidInputError):
            service.list_nodes("Student", limit=0)

        with self.assertRaises(service.InvalidInputError):
            service.list_nodes("Student", limit=True)

    def test_rejects_empty_identifier(self):
        with self.assertRaises(service.InvalidInputError):
            service.get_node("Student", "  ")

    def test_get_node_returns_properties(self):
        session = FakeSession()
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            # This fake supplies the result through the session's run method.
            expected = {"studentId": "S001", "studentName": "Test Student"}
            session.run = lambda query, **params: (
                setattr(session, "last_query", query),
                setattr(session, "last_parameters", params),
                FakeResult({"item": expected}),
            )[-1]

            result = service.get_node("Student", "S001")

        self.assertEqual(result, expected)
        self.assertEqual(session.last_parameters["identifier"], "S001")
        self.assertIn("$identifier", session.last_query)

    def test_get_node_raises_when_missing(self):
        session = FakeSession()
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            with self.assertRaises(service.NotFoundError):
                service.get_node("Student", "MISSING")

    def test_list_nodes_returns_properties(self):
        expected = [{"studentId": "S001"}, {"studentId": "S002"}]
        session = FakeSession(records=[{"item": item} for item in expected])
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            result = service.list_nodes("Student", limit=10)

        self.assertEqual(result, expected)
        self.assertEqual(session.last_parameters, {"limit": 10})
        self.assertIn("$limit", session.last_query)

    def test_create_node_uses_parameterized_properties(self):
        expected = {"studentId": "S001", "studentName": "Test Student"}
        transaction = FakeTransaction(created=expected)
        session = FakeSession(transaction=transaction)
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            result = service.create_node(
                "Student",
                {"studentId": "S001", "studentName": "Test Student"},
            )

        self.assertEqual(result, expected)
        self.assertEqual(
            transaction.calls[1][1]["properties"],
            expected,
        )
        self.assertIn("$properties", transaction.calls[1][0])

    def test_create_node_rejects_existing_identifier(self):
        transaction = FakeTransaction(existing={"existing": object()})
        session = FakeSession(transaction=transaction)
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            with self.assertRaises(service.ConflictError):
                service.create_node("Student", {"studentId": "S001"})

    def test_create_node_requires_identifier(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_node("Student", {"studentName": "Test Student"})

    def test_create_node_rejects_empty_properties(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_node("Student", {})

    def test_create_node_rejects_non_dict_properties(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_node("Student", ["not", "a", "dict"])

    def test_create_node_rejects_invalid_property_key(self):
        with self.assertRaises(service.InvalidInputError):
            service.create_node("Student", {"studentId": "S001", "": "empty_key"})

    def test_create_node_translates_constraint_error(self):
        from neo4j.exceptions import ConstraintError

        session = FakeSession()
        driver = FakeDriver(session)

        def raise_constraint_error(callback):
            raise ConstraintError("Unique constraint violated")

        session.execute_write = raise_constraint_error

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            with self.assertRaises(service.ConflictError):
                service.create_node("Student", {"studentId": "S001"})

    def test_create_node_accepts_all_allowed_properties(self):
        payload = {
            "programId": "P01",
            "programName": "B.Tech CSE",
            "degreeLevel": "BTech",
            "deptId": "D01",
        }
        transaction = FakeTransaction(created=payload)
        session = FakeSession(transaction=transaction)
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            result = service.create_node("Program", payload)

        self.assertEqual(result, payload)

    def test_create_node_rejects_unknown_property(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {
                "deptId": "D01",
                "deptName": "Computer Science",
                "unauthorizedField": "injected",
            })
        self.assertIn("Unsupported property 'unauthorizedField' for Department", str(ctx.exception))

    def test_create_node_rejects_nested_dict_value(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {
                "deptId": "D01",
                "deptName": {"en": "Computer Science"},
            })
        self.assertIn("unsupported value", str(ctx.exception))

    def test_create_node_accepts_valid_primitive_arrays(self):
        payload = {
            "deptId": "D01",
            "deptName": "Computer Science",
        }
        transaction = FakeTransaction(created=payload)
        session = FakeSession(transaction=transaction)
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            result = service.create_node("Department", {
                "deptId": "D01",
                "deptName": "Computer Science",
            })
        self.assertEqual(result, payload)

    def test_create_node_rejects_heterogeneous_array(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {
                "deptId": "D01",
                "deptName": ["Computer Science", 123],
            })
        self.assertIn("unsupported value", str(ctx.exception))

    def test_create_node_rejects_array_with_null(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {
                "deptId": "D01",
                "deptName": ["Computer Science", None],
            })
        self.assertIn("unsupported value", str(ctx.exception))

    def test_create_node_rejects_nested_array(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {
                "deptId": "D01",
                "deptName": [["Computer Science"]],
            })
        self.assertIn("unsupported value", str(ctx.exception))

    def test_create_node_primary_key_whitespace_trimmed(self):
        payload = {"deptId": "  D01  ", "deptName": "Computer Science"}
        transaction = FakeTransaction(created={"deptId": "D01", "deptName": "Computer Science"})
        session = FakeSession(transaction=transaction)
        driver = FakeDriver(session)

        with patch.object(service, "get_driver", return_value=driver), \
             patch.object(service, "get_database_name", return_value="neo4j"):
            service.create_node("Department", payload)

        self.assertEqual(transaction.calls[1][1]["properties"]["deptId"], "D01")

    def test_create_node_rejects_non_string_primary_key(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {"deptId": 101, "deptName": "CS"})
        self.assertIn("non-empty string identifier is required", str(ctx.exception))

    def test_create_node_rejects_empty_string_primary_key(self):
        with self.assertRaises(service.InvalidInputError) as ctx:
            service.create_node("Department", {"deptId": "   ", "deptName": "CS"})
        self.assertIn("non-empty string identifier is required", str(ctx.exception))

    def test_get_graph_data_invalid_limit(self):
        with self.assertRaises(service.InvalidInputError):
            service.get_graph_data(limit="not-a-number")

    def test_get_graph_data_invalid_label(self):
        with self.assertRaises(service.InvalidInputError):
            service.get_graph_data(label="NonExistentLabel")

    def test_get_graph_data_invalid_student_id(self):
        with self.assertRaises(service.InvalidInputError):
            service.get_graph_data(student_id="   ")

    def test_get_graph_data_invalid_search(self):
        with self.assertRaises(service.InvalidInputError):
            service.get_graph_data(search=12345)


if __name__ == "__main__":
    unittest.main()
