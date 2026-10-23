"""Schema-aligned Neo4j graph operations for the DA-3 backend.

Implements academic graph services, input validation, canonical identifiers,
relationship integrity, and business rules for Member 2.
"""

from datetime import date, datetime
from neo4j.exceptions import ConstraintError

try:
    from backend.neo4j_db import get_database_name, get_driver
except ModuleNotFoundError:
    from neo4j_db import get_database_name, get_driver


# Labels and canonical identifiers agreed by the project team.
NODE_IDENTIFIERS = {
    "Department": "deptId",
    "Program": "programId",
    "Student": "studentId",
    "StudentProfile": "studentId",
    "Guardian": "guardianId",
    "Application": "applicationId",
    "Scholarship": "scholarshipId",
    "BankAccount": "accountNo",
    "Disbursement": "disbursementId",
    "Fee": "feeId",
    "PaymentMethod": "methodId",
    "Payment": "paymentId",
}

# Confirmed properties per node label based on Member 1 schema
ALLOWED_PROPERTIES = {
    "Department": {"deptId", "deptName"},
    "Program": {"programId", "programName", "degreeLevel", "deptId"},
    "Student": {
        "studentId",
        "studentName",
        "phone",
        "houseNo",
        "street",
        "city",
        "pin",
        "programId",
    },
    "StudentProfile": {
        "studentId",
        "bloodGroup",
        "nationality",
        "dateOfBirth",
        "email",
    },
    "Guardian": {
        "guardianId",
        "studentId",
        "guardianName",
        "relation",
        "phoneNo",
        "emailId",
    },
    "Application": {
        "applicationId",
        "studentId",
        "applicationDate",
        "applicationStatus",
    },
    "Scholarship": {
        "scholarshipId",
        "applicationId",
        "scholarshipType",
        "amount",
    },
    "BankAccount": {"accountNo", "bankName", "ifsc", "accountType"},
    "Disbursement": {
        "disbursementId",
        "scholarshipId",
        "accountNo",
        "disbursementDate",
        "amount",
        "disbursementMode",
    },
    "Fee": {"feeId", "studentId", "feeAmount", "dueDate"},
    "PaymentMethod": {"methodId", "methodName"},
    "Payment": {
        "paymentId",
        "feeId",
        "scholarshipId",
        "methodId",
        "paymentDate",
        "amountPaid",
        "transactionId",
    },
}

VALID_APPLICATION_STATUSES = {"Pending", "Approved", "Rejected"}


class GraphServiceError(Exception):
    """Base exception for graph service errors."""


class InvalidInputError(GraphServiceError):
    """Raised when a service input is invalid."""


class NotFoundError(GraphServiceError):
    """Raised when a requested graph node does not exist."""


class ConflictError(GraphServiceError):
    """Raised when an operation conflicts with existing data."""


def clean_graph_item(obj):
    """Recursively convert Neo4j objects (Date, Time, Node, Record) into clean JSON-serializable Python types."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: clean_graph_item(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [clean_graph_item(v) for v in obj]
    if hasattr(obj, "iso_format"):
        return obj.iso_format()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


def _validate_label(label):
    """Accept only labels defined by the agreed graph model."""
    if label not in NODE_IDENTIFIERS:
        raise InvalidInputError("Unsupported graph node label.")
    return label


def _validate_identifier(identifier):
    """Require a non-empty string identifier."""
    if not isinstance(identifier, str) or not identifier.strip():
        raise InvalidInputError("A non-empty string identifier is required.")
    return identifier.strip()


def _is_valid_property_value(value):
    """Check if a value is a valid Neo4j property type (scalar primitive or homogeneous primitive list)."""
    if value is None:
        return True
    if isinstance(value, (str, int, float, bool, date, datetime)):
        return True
    if isinstance(value, (list, tuple)):
        if not value:
            return True
        types = set()
        for item in value:
            if item is None:
                return False
            if isinstance(item, bool):
                types.add("bool")
            elif isinstance(item, (int, float)):
                types.add("num")
            elif isinstance(item, str):
                types.add("str")
            elif isinstance(item, (date, datetime)):
                types.add("date")
            else:
                return False
        return len(types) <= 1
    return False


def _validate_properties(label, properties):
    """Validate that properties dictionary contains only allowed properties and valid values for the given label."""
    if not isinstance(properties, dict) or not properties:
        raise InvalidInputError("Properties must be a non-empty object.")

    allowed = ALLOWED_PROPERTIES.get(label)
    for key, value in properties.items():
        if not isinstance(key, str) or not key.strip():
            raise InvalidInputError("Property names must be non-empty strings.")
        if allowed and key not in allowed:
            raise InvalidInputError(f"Unsupported property '{key}' for {label}.")
        if not _is_valid_property_value(value):
            raise InvalidInputError(
                f"Property '{key}' has an unsupported value. "
                "Values must be primitive types or homogeneous primitive arrays."
            )


# ============================================================
# GENERIC NODE CRUD OPERATIONS
# ============================================================


def list_nodes(label, limit=100):
    """List nodes of an approved label, with a bounded result count."""
    label = _validate_label(label)

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")

    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = f"""
        MATCH (n:{label})
        RETURN properties(n) AS item
        ORDER BY n.{NODE_IDENTIFIERS[label]}
        LIMIT $limit
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        return [clean_graph_item(record["item"]) for record in records]


def get_node(label, identifier):
    """Retrieve one node by its agreed identifier property."""
    label = _validate_label(label)
    identifier = _validate_identifier(identifier)
    identifier_property = NODE_IDENTIFIERS[label]

    query = f"""
        MATCH (n:{label} {{{identifier_property}: $identifier}})
        RETURN properties(n) AS item
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, identifier=identifier).single()

    if record is None:
        raise NotFoundError(f"{label} was not found.")

    return clean_graph_item(record["item"])


def create_node(label, properties):
    """Create a generic node without overwriting an existing node."""
    label = _validate_label(label)
    _validate_properties(label, properties)

    identifier_property = NODE_IDENTIFIERS[label]
    raw_id = properties.get(identifier_property)
    identifier = _validate_identifier(raw_id)

    node_properties = dict(properties)
    node_properties[identifier_property] = identifier

    query = f"""
        MATCH (existing:{label} {{{identifier_property}: $identifier}})
        RETURN existing
        LIMIT 1
    """

    create_query = f"""
        CREATE (n:{label})
        SET n = $properties
        RETURN properties(n) AS item
    """

    def create_if_absent(tx):
        existing = tx.run(query, identifier=identifier).single()

        if existing is not None:
            raise ConflictError(
                f"{label} with this identifier already exists."
            )

        record = tx.run(
            create_query,
            properties=node_properties,
        ).single()

        if record is None:
            raise GraphServiceError("Node creation returned no result.")

        return clean_graph_item(record["item"])

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(create_if_absent)
    except ConstraintError as exc:
        raise ConflictError(
            f"{label} with this identifier already exists."
        ) from exc


# ============================================================
# ACADEMIC OPERATIONS: STUDENTS
# ============================================================


def list_students(limit=100):
    """List students with enrolled program and department details."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")

    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = """
        MATCH (s:Student)
        OPTIONAL MATCH (p:Program)-[:HAS_STUDENT]->(s)
        OPTIONAL MATCH (d:Department)-[:HAS_PROGRAM]->(p)
        RETURN properties(s) AS student,
               p.programName AS programName,
               p.degreeLevel AS degreeLevel,
               d.deptName AS deptName
        ORDER BY s.studentId
        LIMIT $limit
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        results = []
        for rec in records:
            student = clean_graph_item(rec["student"]) or {}
            if rec["programName"]:
                student["programName"] = rec["programName"]
            if rec["degreeLevel"]:
                student["degreeLevel"] = rec["degreeLevel"]
            if rec["deptName"]:
                student["deptName"] = rec["deptName"]
            if "studentId" in student:
                student["STUDENTID"] = student["studentId"]
            if "studentName" in student:
                student["STUDENTNAME"] = student["studentName"]
            if "phone" in student:
                student["PHONE"] = student["phone"]
            if "programName" in student:
                student["PROGRAMNAME"] = student["programName"]
            results.append(student)
        return results


def get_student(student_id):
    """Retrieve detailed student information with program and department."""
    student_id = _validate_identifier(student_id)

    query = """
        MATCH (s:Student {studentId: $student_id})
        OPTIONAL MATCH (p:Program)-[:HAS_STUDENT]->(s)
        OPTIONAL MATCH (d:Department)-[:HAS_PROGRAM]->(p)
        RETURN properties(s) AS student,
               properties(p) AS program,
               properties(d) AS department
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, student_id=student_id).single()

    if record is None or record["student"] is None:
        raise NotFoundError(f"Student '{student_id}' was not found.")

    student = clean_graph_item(record["student"])
    if record["program"]:
        student["program"] = clean_graph_item(record["program"])
    if record["department"]:
        student["department"] = clean_graph_item(record["department"])

    return student


def create_student(properties):
    """Create a new student node and link to program if provided."""
    _validate_properties("Student", properties)

    student_id = _validate_identifier(properties.get("studentId"))
    student_name = properties.get("studentName")
    if not isinstance(student_name, str) or not student_name.strip():
        raise InvalidInputError("studentName must be a non-empty string.")

    phone = properties.get("phone")
    if not isinstance(phone, str) or not phone.strip():
        raise InvalidInputError("phone must be a non-empty string.")

    program_id = properties.get("programId")
    if program_id is not None:
        program_id = _validate_identifier(program_id)

    student_properties = dict(properties)
    student_properties["studentId"] = student_id
    student_properties["studentName"] = student_name.strip()
    student_properties["phone"] = phone.strip()
    if program_id:
        student_properties["programId"] = program_id

    def tx_create_student(tx):
        # 1. Check existing student
        existing = tx.run(
            "MATCH (s:Student {studentId: $student_id}) RETURN s LIMIT 1",
            student_id=student_id,
        ).single()
        if existing is not None:
            raise ConflictError(f"Student with identifier '{student_id}' already exists.")

        # 2. If programId is specified, verify program exists
        if program_id:
            prog = tx.run(
                "MATCH (p:Program {programId: $program_id}) RETURN p LIMIT 1",
                program_id=program_id,
            ).single()
            if prog is None:
                raise InvalidInputError(f"Referenced Program '{program_id}' does not exist.")

        # 3. Create Student
        res = tx.run(
            """
            CREATE (s:Student)
            SET s = $properties
            RETURN properties(s) AS item
            """,
            properties=student_properties,
        ).single()

        # 4. Link Program -> Student
        if program_id:
            tx.run(
                """
                MATCH (p:Program {programId: $program_id}), (s:Student {studentId: $student_id})
                MERGE (p)-[:HAS_STUDENT]->(s)
                """,
                program_id=program_id,
                student_id=student_id,
            )

        return clean_graph_item(res["item"])

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_student)
    except ConstraintError as exc:
        raise ConflictError(f"Student with identifier '{student_id}' already exists.") from exc


def get_student_profile(student_id):
    """Retrieve the student's profile via (Student)-[:HAS_PROFILE]->(StudentProfile)."""
    student_id = _validate_identifier(student_id)

    query = """
        MATCH (s:Student {studentId: $student_id})
        OPTIONAL MATCH (s)-[:HAS_PROFILE]->(sp:StudentProfile)
        RETURN s, properties(sp) AS profile
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, student_id=student_id).single()

    if record is None or record["s"] is None:
        raise NotFoundError(f"Student '{student_id}' was not found.")

    if record["profile"] is None:
        raise NotFoundError(f"Profile was not found for student '{student_id}'.")

    return clean_graph_item(record["profile"])


def get_student_guardians(student_id):
    """Retrieve guardians associated with a student via (Student)-[:HAS_GUARDIAN]->(Guardian)."""
    student_id = _validate_identifier(student_id)

    query = """
        MATCH (s:Student {studentId: $student_id})
        OPTIONAL MATCH (s)-[:HAS_GUARDIAN]->(g:Guardian)
        RETURN s, collect(properties(g)) AS guardians
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, student_id=student_id).single()

    if record is None or record["s"] is None:
        raise NotFoundError(f"Student '{student_id}' was not found.")

    raw_guardians = record["guardians"] or []
    # Filter out empty dicts from OPTIONAL MATCH
    guardians = [clean_graph_item(g) for g in raw_guardians if g]
    return guardians


# ============================================================
# ACADEMIC OPERATIONS: DEPARTMENTS & PROGRAMS
# ============================================================


def list_departments():
    """List all departments with program counts."""
    query = """
        MATCH (d:Department)
        OPTIONAL MATCH (d)-[:HAS_PROGRAM]->(p:Program)
        WITH d, count(p) AS programCount
        ORDER BY d.deptId
        RETURN properties(d) AS department, programCount
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query)
        departments = []
        for rec in records:
            dept = clean_graph_item(rec["department"])
            dept["programCount"] = rec["programCount"]
            departments.append(dept)
        return departments


def get_department(dept_id):
    """Retrieve department and its associated programs via (Department)-[:HAS_PROGRAM]->(Program)."""
    dept_id = _validate_identifier(dept_id)

    query = """
        MATCH (d:Department {deptId: $dept_id})
        OPTIONAL MATCH (d)-[:HAS_PROGRAM]->(p:Program)
        RETURN properties(d) AS department, collect(properties(p)) AS programs
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, dept_id=dept_id).single()

    if record is None or record["department"] is None:
        raise NotFoundError(f"Department '{dept_id}' was not found.")

    dept = clean_graph_item(record["department"])
    programs = [clean_graph_item(p) for p in (record["programs"] or []) if p]
    return {"department": dept, "programs": programs}


def list_programs():
    """List all programs with department information."""
    query = """
        MATCH (p:Program)
        OPTIONAL MATCH (d:Department)-[:HAS_PROGRAM]->(p)
        RETURN properties(p) AS program, d.deptName AS deptName
        ORDER BY p.programId
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query)
        programs = []
        for rec in records:
            prog = clean_graph_item(rec["program"])
            if rec["deptName"]:
                prog["deptName"] = rec["deptName"]
            programs.append(prog)
        return programs


def get_program_students(program_id):
    """Retrieve students enrolled in a program via (Program)-[:HAS_STUDENT]->(Student)."""
    program_id = _validate_identifier(program_id)

    query = """
        MATCH (p:Program {programId: $program_id})
        OPTIONAL MATCH (p)-[:HAS_STUDENT]->(s:Student)
        RETURN properties(p) AS program, collect(properties(s)) AS students
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, program_id=program_id).single()

    if record is None or record["program"] is None:
        raise NotFoundError(f"Program '{program_id}' was not found.")

    prog = clean_graph_item(record["program"])
    students = [clean_graph_item(s) for s in (record["students"] or []) if s]
    return {
        "programId": program_id,
        "programName": prog.get("programName"),
        "students": students,
        "count": len(students),
    }


# ============================================================
# ACADEMIC OPERATIONS: APPLICATIONS
# ============================================================


def list_applications(status=None, limit=100):
    """List applications with optional status filter and student details."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")

    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    if status is not None:
        if status not in VALID_APPLICATION_STATUSES:
            raise InvalidInputError(
                f"Invalid status filter. Must be one of: {sorted(list(VALID_APPLICATION_STATUSES))}"
            )

    query = """
        MATCH (a:Application)
        WHERE ($status IS NULL OR a.applicationStatus = $status)
        OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
        OPTIONAL MATCH (a)-[:AWARDS]->(sch:Scholarship)
        RETURN properties(a) AS application,
               s.studentName AS studentName,
               properties(sch) AS scholarship
        ORDER BY a.applicationId
        LIMIT $limit
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, status=status, limit=limit)
        results = []
        for rec in records:
            app = clean_graph_item(rec["application"])
            if rec["studentName"]:
                app["studentName"] = rec["studentName"]
            if rec["scholarship"]:
                app["scholarship"] = clean_graph_item(rec["scholarship"])
            if "applicationId" in app:
                app["APPLICATIONID"] = app["applicationId"]
            if "studentId" in app:
                app["STUDENTID"] = app["studentId"]
            if "studentName" in app:
                app["STUDENTNAME"] = app["studentName"]
            if "applicationDate" in app:
                app["APPLICATIONDATE"] = app["applicationDate"]
            if "applicationStatus" in app:
                app["APPLICATIONSTATUS"] = app["applicationStatus"]
            results.append(app)
        return results


def get_application(application_id):
    """Retrieve an application by ID along with its student and scholarship."""
    application_id = _validate_identifier(application_id)

    query = """
        MATCH (a:Application {applicationId: $application_id})
        OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
        OPTIONAL MATCH (a)-[:AWARDS]->(sch:Scholarship)
        RETURN properties(a) AS application,
               properties(s) AS student,
               properties(sch) AS scholarship
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, application_id=application_id).single()

    if record is None or record["application"] is None:
        raise NotFoundError(f"Application '{application_id}' was not found.")

    res = {
        "application": clean_graph_item(record["application"]),
        "student": clean_graph_item(record["student"]),
        "scholarship": clean_graph_item(record["scholarship"]),
    }
    return res


def create_application(properties):
    """Create an application for an existing student and link via SUBMITTED."""
    _validate_properties("Application", properties)

    application_id = _validate_identifier(properties.get("applicationId"))
    student_id = _validate_identifier(properties.get("studentId"))

    status = properties.get("applicationStatus", "Pending")
    if not isinstance(status, str) or status.strip() not in VALID_APPLICATION_STATUSES:
        raise InvalidInputError(
            f"applicationStatus must be one of: {sorted(list(VALID_APPLICATION_STATUSES))}"
        )
    status = status.strip()

    app_properties = dict(properties)
    app_properties["applicationId"] = application_id
    app_properties["studentId"] = student_id
    app_properties["applicationStatus"] = status

    def tx_create_app(tx):
        # 1. Verify student exists
        student = tx.run(
            "MATCH (s:Student {studentId: $student_id}) RETURN s LIMIT 1",
            student_id=student_id,
        ).single()
        if student is None:
            raise InvalidInputError(f"Referenced Student '{student_id}' does not exist.")

        # 2. Check duplicate application ID
        existing = tx.run(
            "MATCH (a:Application {applicationId: $application_id}) RETURN a LIMIT 1",
            application_id=application_id,
        ).single()
        if existing is not None:
            raise ConflictError(f"Application with identifier '{application_id}' already exists.")

        # 3. Create application
        res = tx.run(
            """
            CREATE (a:Application)
            SET a = $properties
            RETURN properties(a) AS item
            """,
            properties=app_properties,
        ).single()

        # 4. Link (Student)-[:SUBMITTED]->(Application)
        tx.run(
            """
            MATCH (s:Student {studentId: $student_id}), (a:Application {applicationId: $application_id})
            MERGE (s)-[:SUBMITTED]->(a)
            """,
            student_id=student_id,
            application_id=application_id,
        )

        return clean_graph_item(res["item"])

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_app)
    except ConstraintError as exc:
        raise ConflictError(f"Application with identifier '{application_id}' already exists.") from exc


def update_application_status(application_id, new_status):
    """Update status of an existing application ('Pending', 'Approved', 'Rejected')."""
    application_id = _validate_identifier(application_id)

    if not isinstance(new_status, str) or new_status.strip() not in VALID_APPLICATION_STATUSES:
        raise InvalidInputError(
            f"Application status must be one of: {sorted(list(VALID_APPLICATION_STATUSES))}"
        )
    new_status = new_status.strip()

    query = """
        MATCH (a:Application {applicationId: $application_id})
        SET a.applicationStatus = $status
        RETURN properties(a) AS application
    """

    def tx_update_status(tx):
        res = tx.run(query, application_id=application_id, status=new_status).single()
        if res is None or res["application"] is None:
            raise NotFoundError(f"Application '{application_id}' was not found.")
        return clean_graph_item(res["application"])

    with get_driver().session(database=get_database_name()) as session:
        return session.execute_write(tx_update_status)


def get_student_applications(student_id):
    """Retrieve all applications submitted by a student via (Student)-[:SUBMITTED]->(Application)."""
    student_id = _validate_identifier(student_id)

    query = """
        MATCH (s:Student {studentId: $student_id})
        OPTIONAL MATCH (s)-[:SUBMITTED]->(a:Application)
        OPTIONAL MATCH (a)-[:AWARDS]->(sch:Scholarship)
        RETURN s, properties(a) AS application, properties(sch) AS scholarship
        ORDER BY a.applicationId
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, student_id=student_id).data()

    if not records or records[0]["s"] is None:
        raise NotFoundError(f"Student '{student_id}' was not found.")

    applications = []
    for rec in records:
        if rec["application"]:
            app = clean_graph_item(rec["application"])
            if rec["scholarship"]:
                app["scholarship"] = clean_graph_item(rec["scholarship"])
            applications.append(app)

    return applications


# ============================================================
# ACADEMIC OPERATIONS: SCHOLARSHIPS
# ============================================================


def list_scholarships(limit=100):
    """List scholarships with application status and student information."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")

    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = """
        MATCH (sch:Scholarship)
        OPTIONAL MATCH (a:Application)-[:AWARDS]->(sch)
        OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
        RETURN properties(sch) AS scholarship,
               a.applicationStatus AS applicationStatus,
               s.studentId AS studentId,
               s.studentName AS studentName
        ORDER BY sch.scholarshipId
        LIMIT $limit
    """

    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        scholarships = []
        for rec in records:
            item = clean_graph_item(rec["scholarship"])
            if rec["applicationStatus"]:
                item["applicationStatus"] = rec["applicationStatus"]
            if rec["studentId"]:
                item["studentId"] = rec["studentId"]
            if rec["studentName"]:
                item["studentName"] = rec["studentName"]
            if "scholarshipId" in item:
                item["SCHOLARSHIPID"] = item["scholarshipId"]
            if "scholarshipType" in item:
                item["SCHOLARSHIPTYPE"] = item["scholarshipType"]
            if "amount" in item:
                item["AMOUNT"] = item["amount"]
            if "applicationId" in item:
                item["APPLICATIONID"] = item["applicationId"]
            if "studentId" in item:
                item["STUDENTID"] = item["studentId"]
            if "studentName" in item:
                item["STUDENTNAME"] = item["studentName"]
            if "applicationStatus" in item:
                item["APPLICATIONSTATUS"] = item["applicationStatus"]
            scholarships.append(item)
        return scholarships


def get_scholarship(scholarship_id):
    """Retrieve scholarship details, application, student, and linked disbursements."""
    scholarship_id = _validate_identifier(scholarship_id)

    query = """
        MATCH (sch:Scholarship {scholarshipId: $scholarship_id})
        OPTIONAL MATCH (a:Application)-[:AWARDS]->(sch)
        OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
        OPTIONAL MATCH (sch)-[:HAS_DISBURSEMENT]->(d:Disbursement)
        RETURN properties(sch) AS scholarship,
               properties(a) AS application,
               properties(s) AS student,
               collect(properties(d)) AS disbursements
        LIMIT 1
    """

    with get_driver().session(database=get_database_name()) as session:
        record = session.run(query, scholarship_id=scholarship_id).single()

    if record is None or record["scholarship"] is None:
        raise NotFoundError(f"Scholarship '{scholarship_id}' was not found.")

    res = {
        "scholarship": clean_graph_item(record["scholarship"]),
        "application": clean_graph_item(record["application"]),
        "student": clean_graph_item(record["student"]),
        "disbursements": [
            clean_graph_item(d) for d in (record["disbursements"] or []) if d
        ],
    }
    return res


def create_scholarship(properties):
    """Create a scholarship for an approved application without an existing scholarship.

    Enforces:
    1. Scholarship amount must be numeric, finite, and non-negative.
    2. Referenced Application must exist.
    3. Application status must be 'Approved'.
    4. Application must not already have a scholarship.
    5. Duplicate scholarshipId rejected.
    """
    _validate_properties("Scholarship", properties)

    scholarship_id = _validate_identifier(properties.get("scholarshipId"))
    application_id = _validate_identifier(properties.get("applicationId"))

    scholarship_type = properties.get("scholarshipType")
    if not isinstance(scholarship_type, str) or not scholarship_type.strip():
        raise InvalidInputError("scholarshipType must be a non-empty string.")

    amount = properties.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise InvalidInputError("Scholarship amount must be a finite, non-negative number.")
    if amount < 0:
        raise InvalidInputError("Scholarship amount must be non-negative.")

    scholarship_props = dict(properties)
    scholarship_props["scholarshipId"] = scholarship_id
    scholarship_props["applicationId"] = application_id
    scholarship_props["scholarshipType"] = scholarship_type.strip()
    scholarship_props["amount"] = float(amount) if isinstance(amount, int) else amount

    def tx_create_scholarship(tx):
        # 1. Check duplicate scholarshipId
        existing_sch = tx.run(
            "MATCH (s:Scholarship {scholarshipId: $sch_id}) RETURN s LIMIT 1",
            sch_id=scholarship_id,
        ).single()
        if existing_sch is not None:
            raise ConflictError(f"Scholarship with identifier '{scholarship_id}' already exists.")

        # 2. Check referenced application exists
        app_rec = tx.run(
            "MATCH (a:Application {applicationId: $app_id}) RETURN a.applicationStatus AS status LIMIT 1",
            app_id=application_id,
        ).single()
        if app_rec is None:
            raise InvalidInputError(f"Referenced Application '{application_id}' does not exist.")

        # 3. Enforce Approved status rule
        app_status = app_rec["status"]
        if app_status != "Approved":
            raise ConflictError(
                f"Scholarships can only be awarded to approved applications. Current status: '{app_status}'."
            )

        # 4. Enforce at most one scholarship per application rule
        existing_award = tx.run(
            "MATCH (a:Application {applicationId: $app_id})-[:AWARDS]->(s:Scholarship) RETURN s LIMIT 1",
            app_id=application_id,
        ).single()
        if existing_award is not None:
            raise ConflictError(
                f"Application '{application_id}' already has an awarded scholarship."
            )

        # 5. Create Scholarship node
        sch_res = tx.run(
            """
            CREATE (sch:Scholarship)
            SET sch = $properties
            RETURN properties(sch) AS item
            """,
            properties=scholarship_props,
        ).single()

        # 6. Link (Application)-[:AWARDS]->(Scholarship)
        tx.run(
            """
            MATCH (a:Application {applicationId: $app_id}), (sch:Scholarship {scholarshipId: $sch_id})
            MERGE (a)-[:AWARDS]->(sch)
            """,
            app_id=application_id,
            sch_id=scholarship_id,
        )

        return clean_graph_item(sch_res["item"])

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_scholarship)
    except ConstraintError as exc:
        raise ConflictError(f"Scholarship with identifier '{scholarship_id}' already exists.") from exc


# ============================================================
# FINANCIAL SERVICES (FEES, PAYMENTS, DISBURSEMENTS, BANK ACCOUNTS)
# ============================================================

def _format_fee_item(fee_id, student_id, student_name, fee_amount, due_date, amount_paid, outstanding_amount):
    return {
        "feeId": fee_id,
        "FEEID": fee_id,
        "studentId": student_id,
        "STUDENTID": student_id,
        "studentName": student_name,
        "STUDENTNAME": student_name,
        "feeAmount": float(fee_amount) if fee_amount is not None else 0.0,
        "FEEAMOUNT": float(fee_amount) if fee_amount is not None else 0.0,
        "dueDate": str(due_date) if due_date is not None else None,
        "DUEDATE": str(due_date) if due_date is not None else None,
        "amountPaid": float(amount_paid) if amount_paid is not None else 0.0,
        "AMOUNTPAID": float(amount_paid) if amount_paid is not None else 0.0,
        "outstandingAmount": float(outstanding_amount) if outstanding_amount is not None else 0.0,
        "OUTSTANDINGAMOUNT": float(outstanding_amount) if outstanding_amount is not None else 0.0,
    }


def _format_payment_item(payment_id, fee_id, student_id, student_name, scholarship_id, method_id, method_name, payment_date, amount_paid, transaction_id):
    return {
        "paymentId": payment_id,
        "PAYMENTID": payment_id,
        "feeId": fee_id,
        "FEEID": fee_id,
        "studentId": student_id,
        "STUDENTID": student_id,
        "studentName": student_name,
        "STUDENTNAME": student_name,
        "scholarshipId": scholarship_id,
        "SCHOLARSHIPID": scholarship_id,
        "methodId": method_id,
        "METHODID": method_id,
        "methodName": method_name,
        "METHODNAME": method_name,
        "paymentDate": str(payment_date) if payment_date is not None else None,
        "PAYMENTDATE": str(payment_date) if payment_date is not None else None,
        "amountPaid": float(amount_paid) if amount_paid is not None else 0.0,
        "AMOUNTPAID": float(amount_paid) if amount_paid is not None else 0.0,
        "transactionId": transaction_id,
        "TRANSACTIONID": transaction_id,
    }


def _format_disbursement_item(disbursement_id, scholarship_id, application_id, student_id, student_name, account_no, bank_name, ifsc, disbursement_date, amount, disbursement_mode):
    return {
        "disbursementId": disbursement_id,
        "DISBURSEMENTID": disbursement_id,
        "scholarshipId": scholarship_id,
        "SCHOLARSHIPID": scholarship_id,
        "applicationId": application_id,
        "APPLICATIONID": application_id,
        "studentId": student_id,
        "STUDENTID": student_id,
        "studentName": student_name,
        "STUDENTNAME": student_name,
        "accountNo": account_no,
        "ACCOUNTNO": account_no,
        "bankName": bank_name,
        "BANKNAME": bank_name,
        "ifsc": ifsc,
        "IFSC": ifsc,
        "disbursementDate": str(disbursement_date) if disbursement_date is not None else None,
        "DISBURSEMENTDATE": str(disbursement_date) if disbursement_date is not None else None,
        "amount": float(amount) if amount is not None else 0.0,
        "AMOUNT": float(amount) if amount is not None else 0.0,
        "disbursementMode": disbursement_mode,
        "DISBURSEMENTMODE": disbursement_mode,
    }


def _format_bank_account_item(account_no, bank_name, ifsc, account_type):
    return {
        "accountNo": account_no,
        "ACCOUNTNO": account_no,
        "bankName": bank_name,
        "BANKNAME": bank_name,
        "ifsc": ifsc,
        "IFSC": ifsc,
        "accountType": account_type or "Savings",
        "ACCOUNTTYPE": account_type or "Savings",
    }


def list_fees(limit=100):
    """List student fees with student details, amount paid, and outstanding balance."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")
    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = """
        MATCH (f:Fee)
        OPTIONAL MATCH (s:Student)-[:HAS_FEE]->(f)
        CALL (f) {
            OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
            RETURN coalesce(sum(p.amountPaid), 0) AS amountPaid
        }
        RETURN
            f.feeId AS feeId,
            f.studentId AS studentId,
            s.studentName AS studentName,
            f.feeAmount AS feeAmount,
            toString(f.dueDate) AS dueDate,
            amountPaid,
            f.feeAmount - amountPaid AS outstandingAmount
        ORDER BY f.feeId
        LIMIT $limit
    """
    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        results = []
        for rec in records:
            results.append(_format_fee_item(
                fee_id=rec["feeId"],
                student_id=rec["studentId"],
                student_name=rec["studentName"],
                fee_amount=rec["feeAmount"],
                due_date=rec["dueDate"],
                amount_paid=rec["amountPaid"],
                outstanding_amount=rec["outstandingAmount"],
            ))
        return results


def get_fee(fee_id):
    """Retrieve detailed fee record by feeId including payment history."""
    fee_id = _validate_identifier(fee_id)
    query = """
        MATCH (f:Fee {feeId: $fee_id})
        OPTIONAL MATCH (s:Student)-[:HAS_FEE]->(f)
        CALL (f, s) {
            OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
            OPTIONAL MATCH (p)-[:PAID_VIA]->(m:PaymentMethod)
            OPTIONAL MATCH (p)-[:USES_SCHOLARSHIP]->(sch:Scholarship)
            RETURN collect(DISTINCT CASE
                WHEN p IS NULL THEN null
                ELSE {
                    paymentId: p.paymentId,
                    feeId: p.feeId,
                    studentId: f.studentId,
                    studentName: s.studentName,
                    scholarshipId: sch.scholarshipId,
                    methodId: m.methodId,
                    methodName: m.methodName,
                    paymentDate: toString(p.paymentDate),
                    amountPaid: p.amountPaid,
                    transactionId: p.transactionId
                }
            END) AS payments,
            coalesce(sum(p.amountPaid), 0) AS totalPaid
        }
        RETURN
            f.feeId AS feeId,
            f.studentId AS studentId,
            s.studentName AS studentName,
            f.feeAmount AS feeAmount,
            toString(f.dueDate) AS dueDate,
            totalPaid AS amountPaid,
            f.feeAmount - totalPaid AS outstandingAmount,
            [p IN payments WHERE p IS NOT NULL] AS paymentsList
        LIMIT 1
    """
    with get_driver().session(database=get_database_name()) as session:
        rec = session.run(query, fee_id=fee_id).single()
    if rec is None or rec["feeId"] is None:
        raise NotFoundError(f"Fee '{fee_id}' was not found.")

    fee_item = _format_fee_item(
        fee_id=rec["feeId"],
        student_id=rec["studentId"],
        student_name=rec["studentName"],
        fee_amount=rec["feeAmount"],
        due_date=rec["dueDate"],
        amount_paid=rec["amountPaid"],
        outstanding_amount=rec["outstandingAmount"],
    )
    fee_item["payments"] = [
        _format_payment_item(
            payment_id=p["paymentId"],
            fee_id=p["feeId"],
            student_id=p["studentId"],
            student_name=p["studentName"],
            scholarship_id=p["scholarshipId"],
            method_id=p["methodId"],
            method_name=p["methodName"],
            payment_date=p["paymentDate"],
            amount_paid=p["amountPaid"],
            transaction_id=p["transactionId"],
        )
        for p in rec["paymentsList"]
    ]
    return fee_item


def get_student_fees(student_id):
    """Retrieve all fees associated with a specific student."""
    student_id = _validate_identifier(student_id)
    check_query = "MATCH (s:Student {studentId: $student_id}) RETURN s.studentName AS studentName LIMIT 1"
    query = """
        MATCH (s:Student {studentId: $student_id})-[:HAS_FEE]->(f:Fee)
        CALL (f) {
            OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
            RETURN coalesce(sum(p.amountPaid), 0) AS amountPaid
        }
        RETURN
            f.feeId AS feeId,
            f.studentId AS studentId,
            s.studentName AS studentName,
            f.feeAmount AS feeAmount,
            toString(f.dueDate) AS dueDate,
            amountPaid,
            f.feeAmount - amountPaid AS outstandingAmount
        ORDER BY f.feeId
    """
    with get_driver().session(database=get_database_name()) as session:
        student_rec = session.run(check_query, student_id=student_id).single()
        if student_rec is None:
            raise NotFoundError(f"Student '{student_id}' was not found.")
        records = session.run(query, student_id=student_id)
        results = []
        for rec in records:
            results.append(_format_fee_item(
                fee_id=rec["feeId"],
                student_id=rec["studentId"],
                student_name=rec["studentName"],
                fee_amount=rec["feeAmount"],
                due_date=rec["dueDate"],
                amount_paid=rec["amountPaid"],
                outstanding_amount=rec["outstandingAmount"],
            ))
        return results


def create_fee(properties):
    """Create a student fee record linked to an existing student."""
    if not isinstance(properties, dict):
        raise InvalidInputError("Fee properties must be a dictionary.")

    fee_id_raw = properties.get("fee_id") or properties.get("feeId")
    student_id_raw = properties.get("student_id") or properties.get("studentId")
    fee_amount_raw = properties.get("fee_amount") if "fee_amount" in properties else properties.get("feeAmount")
    due_date_raw = properties.get("due_date") or properties.get("dueDate")

    if not fee_id_raw:
        raise InvalidInputError("Missing required field: fee_id")
    if not student_id_raw:
        raise InvalidInputError("Missing required field: student_id")
    if fee_amount_raw is None:
        raise InvalidInputError("Missing required field: fee_amount")
    if not due_date_raw:
        raise InvalidInputError("Missing required field: due_date")

    fee_id = _validate_identifier(str(fee_id_raw))
    student_id = _validate_identifier(str(student_id_raw))

    if isinstance(fee_amount_raw, bool) or not isinstance(fee_amount_raw, (int, float)):
        try:
            fee_amount = float(fee_amount_raw)
        except (ValueError, TypeError):
            raise InvalidInputError("Fee amount must be a valid number.")
    else:
        fee_amount = float(fee_amount_raw)

    if fee_amount < 0:
        raise InvalidInputError("Fee amount cannot be negative.")

    due_date_str = str(due_date_raw).strip()

    def tx_create_fee(tx):
        # 1. Check duplicate feeId
        existing_fee = tx.run(
            "MATCH (f:Fee {feeId: $fee_id}) RETURN f LIMIT 1",
            fee_id=fee_id,
        ).single()
        if existing_fee is not None:
            raise ConflictError(f"Fee with identifier '{fee_id}' already exists.")

        # 2. Check referenced Student exists
        student_rec = tx.run(
            "MATCH (s:Student {studentId: $student_id}) RETURN s.studentName AS name LIMIT 1",
            student_id=student_id,
        ).single()
        if student_rec is None:
            raise NotFoundError(f"Student '{student_id}' not found.")

        student_name = student_rec["name"]

        # 3. Create Fee node and relationship (Student)-[:HAS_FEE]->(Fee)
        tx.run(
            """
            MATCH (s:Student {studentId: $student_id})
            CREATE (f:Fee {
                feeId: $fee_id,
                studentId: $student_id,
                feeAmount: $fee_amount,
                dueDate: date($due_date)
            })
            MERGE (s)-[:HAS_FEE]->(f)
            """,
            student_id=student_id,
            fee_id=fee_id,
            fee_amount=fee_amount,
            due_date=due_date_str,
        )

        return _format_fee_item(
            fee_id=fee_id,
            student_id=student_id,
            student_name=student_name,
            fee_amount=fee_amount,
            due_date=due_date_str,
            amount_paid=0.0,
            outstanding_amount=fee_amount,
        )

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_fee)
    except ConstraintError as exc:
        raise ConflictError(f"Fee with identifier '{fee_id}' already exists.") from exc


def list_payments(limit=100):
    """List fee payments with linked student, fee, payment method, and optional scholarship."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")
    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = """
        MATCH (p:Payment)
        OPTIONAL MATCH (f:Fee)-[:HAS_PAYMENT]->(p)
        OPTIONAL MATCH (s:Student)-[:HAS_FEE]->(f)
        OPTIONAL MATCH (p)-[:PAID_VIA]->(m:PaymentMethod)
        OPTIONAL MATCH (p)-[:USES_SCHOLARSHIP]->(sch:Scholarship)
        RETURN
            p.paymentId AS paymentId,
            p.feeId AS feeId,
            f.studentId AS studentId,
            s.studentName AS studentName,
            p.scholarshipId AS scholarshipId,
            m.methodId AS methodId,
            m.methodName AS methodName,
            toString(p.paymentDate) AS paymentDate,
            p.amountPaid AS amountPaid,
            p.transactionId AS transactionId
        ORDER BY p.paymentId
        LIMIT $limit
    """
    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        results = []
        for rec in records:
            results.append(_format_payment_item(
                payment_id=rec["paymentId"],
                fee_id=rec["feeId"],
                student_id=rec["studentId"],
                student_name=rec["studentName"],
                scholarship_id=rec["scholarshipId"],
                method_id=rec["methodId"],
                method_name=rec["methodName"],
                payment_date=rec["paymentDate"],
                amount_paid=rec["amountPaid"],
                transaction_id=rec["transactionId"],
            ))
        return results


def get_payment(payment_id):
    """Retrieve detailed payment record by paymentId."""
    payment_id = _validate_identifier(payment_id)
    query = """
        MATCH (p:Payment {paymentId: $payment_id})
        OPTIONAL MATCH (f:Fee)-[:HAS_PAYMENT]->(p)
        OPTIONAL MATCH (s:Student)-[:HAS_FEE]->(f)
        OPTIONAL MATCH (p)-[:PAID_VIA]->(m:PaymentMethod)
        OPTIONAL MATCH (p)-[:USES_SCHOLARSHIP]->(sch:Scholarship)
        RETURN
            p.paymentId AS paymentId,
            p.feeId AS feeId,
            f.studentId AS studentId,
            s.studentName AS studentName,
            p.scholarshipId AS scholarshipId,
            m.methodId AS methodId,
            m.methodName AS methodName,
            toString(p.paymentDate) AS paymentDate,
            p.amountPaid AS amountPaid,
            p.transactionId AS transactionId
        LIMIT 1
    """
    with get_driver().session(database=get_database_name()) as session:
        rec = session.run(query, payment_id=payment_id).single()
    if rec is None or rec["paymentId"] is None:
        raise NotFoundError(f"Payment '{payment_id}' was not found.")
    return _format_payment_item(
        payment_id=rec["paymentId"],
        fee_id=rec["feeId"],
        student_id=rec["studentId"],
        student_name=rec["studentName"],
        scholarship_id=rec["scholarshipId"],
        method_id=rec["methodId"],
        method_name=rec["methodName"],
        payment_date=rec["paymentDate"],
        amount_paid=rec["amountPaid"],
        transaction_id=rec["transactionId"],
    )


def get_student_payments(student_id):
    """Retrieve all payments made for fees of a specific student."""
    student_id = _validate_identifier(student_id)
    check_query = "MATCH (s:Student {studentId: $student_id}) RETURN s.studentName AS name LIMIT 1"
    query = """
        MATCH (s:Student {studentId: $student_id})-[:HAS_FEE]->(f:Fee)-[:HAS_PAYMENT]->(p:Payment)
        OPTIONAL MATCH (p)-[:PAID_VIA]->(m:PaymentMethod)
        OPTIONAL MATCH (p)-[:USES_SCHOLARSHIP]->(sch:Scholarship)
        RETURN
            p.paymentId AS paymentId,
            p.feeId AS feeId,
            s.studentId AS studentId,
            s.studentName AS studentName,
            p.scholarshipId AS scholarshipId,
            m.methodId AS methodId,
            m.methodName AS methodName,
            toString(p.paymentDate) AS paymentDate,
            p.amountPaid AS amountPaid,
            p.transactionId AS transactionId
        ORDER BY p.paymentDate DESC, p.paymentId
    """
    with get_driver().session(database=get_database_name()) as session:
        student_rec = session.run(check_query, student_id=student_id).single()
        if student_rec is None:
            raise NotFoundError(f"Student '{student_id}' was not found.")
        records = session.run(query, student_id=student_id)
        results = []
        for rec in records:
            results.append(_format_payment_item(
                payment_id=rec["paymentId"],
                fee_id=rec["feeId"],
                student_id=rec["studentId"],
                student_name=rec["studentName"],
                scholarship_id=rec["scholarshipId"],
                method_id=rec["methodId"],
                method_name=rec["methodName"],
                payment_date=rec["paymentDate"],
                amount_paid=rec["amountPaid"],
                transaction_id=rec["transactionId"],
            ))
        return results


def create_payment(properties):
    """Create a fee payment with relationships to Fee, PaymentMethod, and optional Scholarship.

    Enforces:
    1. Required fields: payment_id, fee_id, method_id, payment_date, amount_paid, transaction_id.
    2. Payment amount must be numeric, finite, and strictly greater than zero.
    3. Duplicate paymentId is rejected.
    4. Referenced Fee must exist.
    5. Referenced PaymentMethod must exist.
    6. Referenced Scholarship must exist if provided.
    7. Payment must not cause total payments to exceed fee amount (Oracle PL/SQL TRG_CHECK_FEE_PAYMENT rule).
    """
    if not isinstance(properties, dict):
        raise InvalidInputError("Payment properties must be a dictionary.")

    payment_id_raw = properties.get("payment_id") or properties.get("paymentId")
    fee_id_raw = properties.get("fee_id") or properties.get("feeId")
    method_id_raw = properties.get("method_id") or properties.get("methodId")
    payment_date_raw = properties.get("payment_date") or properties.get("paymentDate")
    amount_paid_raw = properties.get("amount_paid") if "amount_paid" in properties else properties.get("amountPaid")
    transaction_id_raw = properties.get("transaction_id") or properties.get("transactionId")
    scholarship_id_raw = properties.get("scholarship_id") or properties.get("scholarshipId")

    if not payment_id_raw:
        raise InvalidInputError("Missing required field: payment_id")
    if not fee_id_raw:
        raise InvalidInputError("Missing required field: fee_id")
    if not method_id_raw:
        raise InvalidInputError("Missing required field: method_id")
    if not payment_date_raw:
        raise InvalidInputError("Missing required field: payment_date")
    if amount_paid_raw is None:
        raise InvalidInputError("Missing required field: amount_paid")
    if not transaction_id_raw:
        raise InvalidInputError("Missing required field: transaction_id")

    payment_id = _validate_identifier(str(payment_id_raw))
    fee_id = _validate_identifier(str(fee_id_raw))
    method_id = _validate_identifier(str(method_id_raw))
    transaction_id = _validate_identifier(str(transaction_id_raw))
    payment_date_str = str(payment_date_raw).strip()

    if isinstance(amount_paid_raw, bool) or not isinstance(amount_paid_raw, (int, float)):
        try:
            amount_paid = float(amount_paid_raw)
        except (ValueError, TypeError):
            raise InvalidInputError("Payment amount must be a valid number.")
    else:
        amount_paid = float(amount_paid_raw)

    if amount_paid <= 0:
        raise InvalidInputError("Payment amount must be greater than zero.")

    scholarship_id = None
    if scholarship_id_raw and str(scholarship_id_raw).strip():
        scholarship_id = str(scholarship_id_raw).strip()

    def tx_create_payment(tx):
        # 1. Check duplicate paymentId
        existing_p = tx.run(
            "MATCH (p:Payment {paymentId: $payment_id}) RETURN p LIMIT 1",
            payment_id=payment_id,
        ).single()
        if existing_p is not None:
            raise ConflictError(f"Payment with identifier '{payment_id}' already exists.")

        # 2. Check Fee exists and verify payment does not exceed fee amount
        fee_rec = tx.run(
            """
            MATCH (f:Fee {feeId: $fee_id})
            OPTIONAL MATCH (s:Student)-[:HAS_FEE]->(f)
            OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
            RETURN f.feeAmount AS feeAmount,
                   f.studentId AS studentId,
                   s.studentName AS studentName,
                   coalesce(sum(p.amountPaid), 0) AS totalPaid
            LIMIT 1
            """,
            fee_id=fee_id,
        ).single()

        if fee_rec is None or fee_rec["feeAmount"] is None:
            raise NotFoundError("Fee record does not exist.")

        fee_amount = fee_rec["feeAmount"]
        total_paid = fee_rec["totalPaid"]
        student_id = fee_rec["studentId"]
        student_name = fee_rec["studentName"]

        if total_paid + amount_paid > fee_amount:
            raise InvalidInputError("Payment exceeds the total fee amount.")

        # 3. Check PaymentMethod exists
        method_rec = tx.run(
            "MATCH (m:PaymentMethod {methodId: $method_id}) RETURN m.methodName AS methodName LIMIT 1",
            method_id=method_id,
        ).single()
        if method_rec is None:
            raise NotFoundError("Payment method not found.")

        method_name = method_rec["methodName"]

        # 4. Check Scholarship exists if specified
        if scholarship_id:
            sch_rec = tx.run(
                "MATCH (sch:Scholarship {scholarshipId: $sch_id}) RETURN sch LIMIT 1",
                sch_id=scholarship_id,
            ).single()
            if sch_rec is None:
                raise NotFoundError("Scholarship not found.")

        # 5. Create Payment node and relationships
        tx.run(
            """
            MATCH (f:Fee {feeId: $fee_id}), (m:PaymentMethod {methodId: $method_id})
            CREATE (p:Payment {
                paymentId: $payment_id,
                feeId: $fee_id,
                methodId: $method_id,
                scholarshipId: $scholarship_id,
                paymentDate: date($payment_date),
                amountPaid: $amount_paid,
                transactionId: $transaction_id
            })
            MERGE (f)-[:HAS_PAYMENT]->(p)
            MERGE (p)-[:PAID_VIA]->(m)
            WITH p
            OPTIONAL MATCH (sch:Scholarship {scholarshipId: $scholarship_id})
            FOREACH (_ IN CASE WHEN sch IS NOT NULL THEN [1] ELSE [] END |
                MERGE (p)-[:USES_SCHOLARSHIP]->(sch)
            )
            """,
            fee_id=fee_id,
            method_id=method_id,
            payment_id=payment_id,
            scholarship_id=scholarship_id,
            payment_date=payment_date_str,
            amount_paid=amount_paid,
            transaction_id=transaction_id,
        )

        return _format_payment_item(
            payment_id=payment_id,
            fee_id=fee_id,
            student_id=student_id,
            student_name=student_name,
            scholarship_id=scholarship_id,
            method_id=method_id,
            method_name=method_name,
            payment_date=payment_date_str,
            amount_paid=amount_paid,
            transaction_id=transaction_id,
        )

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_payment)
    except ConstraintError as exc:
        raise ConflictError(f"Payment with identifier '{payment_id}' already exists.") from exc


def list_disbursements(limit=100):
    """List scholarship disbursements with student and bank account details."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")
    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = """
        MATCH (d:Disbursement)
        OPTIONAL MATCH (sch:Scholarship)-[:HAS_DISBURSEMENT]->(d)
        OPTIONAL MATCH (a:Application)-[:AWARDS]->(sch)
        OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
        OPTIONAL MATCH (d)-[:TO_ACCOUNT]->(b:BankAccount)
        RETURN
            d.disbursementId AS disbursementId,
            d.scholarshipId AS scholarshipId,
            a.applicationId AS applicationId,
            s.studentId AS studentId,
            s.studentName AS studentName,
            d.accountNo AS accountNo,
            b.bankName AS bankName,
            b.ifsc AS ifsc,
            toString(d.disbursementDate) AS disbursementDate,
            d.amount AS amount,
            d.disbursementMode AS disbursementMode
        ORDER BY d.disbursementDate DESC, d.disbursementId
        LIMIT $limit
    """
    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        results = []
        for rec in records:
            results.append(_format_disbursement_item(
                disbursement_id=rec["disbursementId"],
                scholarship_id=rec["scholarshipId"],
                application_id=rec["applicationId"],
                student_id=rec["studentId"],
                student_name=rec["studentName"],
                account_no=rec["accountNo"],
                bank_name=rec["bankName"],
                ifsc=rec["ifsc"],
                disbursement_date=rec["disbursementDate"],
                amount=rec["amount"],
                disbursement_mode=rec["disbursementMode"],
            ))
        return results


def get_disbursement(disbursement_id):
    """Retrieve detailed disbursement record by disbursementId."""
    disbursement_id = _validate_identifier(disbursement_id)
    query = """
        MATCH (d:Disbursement {disbursementId: $disbursement_id})
        OPTIONAL MATCH (sch:Scholarship)-[:HAS_DISBURSEMENT]->(d)
        OPTIONAL MATCH (a:Application)-[:AWARDS]->(sch)
        OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
        OPTIONAL MATCH (d)-[:TO_ACCOUNT]->(b:BankAccount)
        RETURN
            d.disbursementId AS disbursementId,
            d.scholarshipId AS scholarshipId,
            a.applicationId AS applicationId,
            s.studentId AS studentId,
            s.studentName AS studentName,
            d.accountNo AS accountNo,
            b.bankName AS bankName,
            b.ifsc AS ifsc,
            toString(d.disbursementDate) AS disbursementDate,
            d.amount AS amount,
            d.disbursementMode AS disbursementMode
        LIMIT 1
    """
    with get_driver().session(database=get_database_name()) as session:
        rec = session.run(query, disbursement_id=disbursement_id).single()
    if rec is None or rec["disbursementId"] is None:
        raise NotFoundError(f"Disbursement '{disbursement_id}' was not found.")
    return _format_disbursement_item(
        disbursement_id=rec["disbursementId"],
        scholarship_id=rec["scholarshipId"],
        application_id=rec["applicationId"],
        student_id=rec["studentId"],
        student_name=rec["studentName"],
        account_no=rec["accountNo"],
        bank_name=rec["bankName"],
        ifsc=rec["ifsc"],
        disbursement_date=rec["disbursementDate"],
        amount=rec["amount"],
        disbursement_mode=rec["disbursementMode"],
    )


def create_disbursement(properties):
    """Create a scholarship disbursement linked to Scholarship and BankAccount."""
    if not isinstance(properties, dict):
        raise InvalidInputError("Disbursement properties must be a dictionary.")

    disbursement_id_raw = properties.get("disbursement_id") or properties.get("disbursementId")
    scholarship_id_raw = properties.get("scholarship_id") or properties.get("scholarshipId")
    account_no_raw = properties.get("account_no") or properties.get("accountNo")
    disbursement_date_raw = properties.get("disbursement_date") or properties.get("disbursementDate")
    amount_raw = properties.get("amount")
    disbursement_mode_raw = properties.get("disbursement_mode") or properties.get("disbursementMode")

    if not disbursement_id_raw:
        raise InvalidInputError("Missing required field: disbursement_id")
    if not scholarship_id_raw:
        raise InvalidInputError("Missing required field: scholarship_id")
    if not account_no_raw:
        raise InvalidInputError("Missing required field: account_no")
    if not disbursement_date_raw:
        raise InvalidInputError("Missing required field: disbursement_date")
    if amount_raw is None:
        raise InvalidInputError("Missing required field: amount")
    if not disbursement_mode_raw:
        raise InvalidInputError("Missing required field: disbursement_mode")

    disbursement_id = _validate_identifier(str(disbursement_id_raw))
    scholarship_id = _validate_identifier(str(scholarship_id_raw))
    account_no = _validate_identifier(str(account_no_raw))
    disbursement_date_str = str(disbursement_date_raw).strip()
    disbursement_mode = str(disbursement_mode_raw).strip()

    if disbursement_mode not in ["Bank Transfer", "Direct Transfer"]:
        raise InvalidInputError("Disbursement mode must be Bank Transfer or Direct Transfer")

    if isinstance(amount_raw, bool) or not isinstance(amount_raw, (int, float)):
        try:
            amount = float(amount_raw)
        except (ValueError, TypeError):
            raise InvalidInputError("Amount must be a valid number.")
    else:
        amount = float(amount_raw)

    if amount <= 0:
        raise InvalidInputError("Amount must be greater than zero.")

    def tx_create_disbursement(tx):
        # 1. Check duplicate disbursementId
        existing_d = tx.run(
            "MATCH (d:Disbursement {disbursementId: $disbursement_id}) RETURN d LIMIT 1",
            disbursement_id=disbursement_id,
        ).single()
        if existing_d is not None:
            raise ConflictError(f"Disbursement with identifier '{disbursement_id}' already exists.")

        # 2. Check Scholarship exists and verify total disbursed <= scholarship amount
        sch_rec = tx.run(
            """
            MATCH (sch:Scholarship {scholarshipId: $sch_id})
            OPTIONAL MATCH (a:Application)-[:AWARDS]->(sch)
            OPTIONAL MATCH (s:Student)-[:SUBMITTED]->(a)
            OPTIONAL MATCH (sch)-[:HAS_DISBURSEMENT]->(d:Disbursement)
            RETURN sch.amount AS scholarshipAmount,
                   a.applicationId AS applicationId,
                   s.studentId AS studentId,
                   s.studentName AS studentName,
                   coalesce(sum(d.amount), 0) AS totalDisbursed
            LIMIT 1
            """,
            sch_id=scholarship_id,
        ).single()

        if sch_rec is None or sch_rec["scholarshipAmount"] is None:
            raise NotFoundError("Scholarship not found")

        scholarship_amount = sch_rec["scholarshipAmount"]
        total_disbursed = sch_rec["totalDisbursed"]
        application_id = sch_rec["applicationId"]
        student_id = sch_rec["studentId"]
        student_name = sch_rec["studentName"]

        if total_disbursed + amount > scholarship_amount:
            raise InvalidInputError("Disbursement exceeds the total scholarship amount.")

        # 3. Check BankAccount exists
        acc_rec = tx.run(
            "MATCH (b:BankAccount {accountNo: $account_no}) RETURN b.bankName AS bankName, b.ifsc AS ifsc LIMIT 1",
            account_no=account_no,
        ).single()
        if acc_rec is None:
            raise NotFoundError("Bank account not found")

        bank_name = acc_rec["bankName"]
        ifsc = acc_rec["ifsc"]

        # 4. Create Disbursement node and relationships
        tx.run(
            """
            MATCH (sch:Scholarship {scholarshipId: $sch_id}), (b:BankAccount {accountNo: $account_no})
            CREATE (d:Disbursement {
                disbursementId: $disbursement_id,
                scholarshipId: $sch_id,
                accountNo: $account_no,
                disbursementDate: date($disbursement_date),
                amount: $amount,
                disbursementMode: $disbursement_mode
            })
            MERGE (sch)-[:HAS_DISBURSEMENT]->(d)
            MERGE (d)-[:TO_ACCOUNT]->(b)
            """,
            sch_id=scholarship_id,
            account_no=account_no,
            disbursement_id=disbursement_id,
            disbursement_date=disbursement_date_str,
            amount=amount,
            disbursement_mode=disbursement_mode,
        )

        return _format_disbursement_item(
            disbursement_id=disbursement_id,
            scholarship_id=scholarship_id,
            application_id=application_id,
            student_id=student_id,
            student_name=student_name,
            account_no=account_no,
            bank_name=bank_name,
            ifsc=ifsc,
            disbursement_date=disbursement_date_str,
            amount=amount,
            disbursement_mode=disbursement_mode,
        )

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_disbursement)
    except ConstraintError as exc:
        raise ConflictError(f"Disbursement with identifier '{disbursement_id}' already exists.") from exc


def list_bank_accounts(limit=100):
    """List bank accounts in the system."""
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidInputError("Limit must be an integer.")
    if not 1 <= limit <= 500:
        raise InvalidInputError("Limit must be between 1 and 500.")

    query = """
        MATCH (b:BankAccount)
        RETURN b.accountNo AS accountNo,
               b.bankName AS bankName,
               b.ifsc AS ifsc,
               b.accountType AS accountType
        ORDER BY b.accountNo
        LIMIT $limit
    """
    with get_driver().session(database=get_database_name()) as session:
        records = session.run(query, limit=limit)
        results = []
        for rec in records:
            results.append(_format_bank_account_item(
                account_no=rec["accountNo"],
                bank_name=rec["bankName"],
                ifsc=rec["ifsc"],
                account_type=rec["accountType"] or "Savings",
            ))
        return results


def get_bank_account(account_no):
    """Retrieve details for a single bank account."""
    account_no = _validate_identifier(account_no)
    query = """
        MATCH (b:BankAccount {accountNo: $account_no})
        RETURN b.accountNo AS accountNo,
               b.bankName AS bankName,
               b.ifsc AS ifsc,
               b.accountType AS accountType
        LIMIT 1
    """
    with get_driver().session(database=get_database_name()) as session:
        rec = session.run(query, account_no=account_no).single()
    if rec is None or rec["accountNo"] is None:
        raise NotFoundError(f"Bank account '{account_no}' was not found.")
    return _format_bank_account_item(
        account_no=rec["accountNo"],
        bank_name=rec["bankName"],
        ifsc=rec["ifsc"],
        account_type=rec["accountType"] or "Savings",
    )


def create_bank_account(properties):
    """Create a new bank account node in the graph."""
    if not isinstance(properties, dict):
        raise InvalidInputError("Bank account properties must be a dictionary.")

    account_no_raw = properties.get("account_no") or properties.get("accountNo")
    bank_name_raw = properties.get("bank_name") or properties.get("bankName")
    ifsc_raw = properties.get("ifsc") or properties.get("IFSC")
    account_type_raw = properties.get("account_type") or properties.get("accountType") or "Savings"

    if not account_no_raw:
        raise InvalidInputError("Missing required field: account_no")
    if not bank_name_raw:
        raise InvalidInputError("Missing required field: bank_name")
    if not ifsc_raw:
        raise InvalidInputError("Missing required field: ifsc")

    account_no = _validate_identifier(str(account_no_raw))
    bank_name = str(bank_name_raw).strip()
    ifsc = str(ifsc_raw).strip()
    account_type = str(account_type_raw).strip()

    def tx_create_bank_account(tx):
        existing = tx.run(
            "MATCH (b:BankAccount {accountNo: $account_no}) RETURN b LIMIT 1",
            account_no=account_no,
        ).single()
        if existing is not None:
            raise ConflictError(f"Bank account '{account_no}' already exists.")

        tx.run(
            """
            CREATE (b:BankAccount {
                accountNo: $account_no,
                bankName: $bank_name,
                ifsc: $ifsc,
                accountType: $account_type
            })
            """,
            account_no=account_no,
            bank_name=bank_name,
            ifsc=ifsc,
            account_type=account_type,
        )
        return _format_bank_account_item(
            account_no=account_no,
            bank_name=bank_name,
            ifsc=ifsc,
            account_type=account_type,
        )

    try:
        with get_driver().session(database=get_database_name()) as session:
            return session.execute_write(tx_create_bank_account)
    except ConstraintError as exc:
        raise ConflictError(f"Bank account '{account_no}' already exists.") from exc


def get_student_scholarships(student_id):
    """Retrieve all scholarships awarded to a specific student."""
    student_id = _validate_identifier(student_id)
    check_query = "MATCH (s:Student {studentId: $student_id}) RETURN s.studentName AS name LIMIT 1"
    query = """
        MATCH (s:Student {studentId: $student_id})-[:SUBMITTED]->(a:Application)-[:AWARDS]->(sch:Scholarship)
        RETURN
            sch.scholarshipId AS scholarshipId,
            s.studentId AS studentId,
            s.studentName AS studentName,
            sch.scholarshipType AS scholarshipType,
            sch.amount AS amount,
            a.applicationId AS applicationId,
            a.applicationStatus AS applicationStatus
        ORDER BY sch.scholarshipId
    """
    with get_driver().session(database=get_database_name()) as session:
        student_rec = session.run(check_query, student_id=student_id).single()
        if student_rec is None:
            raise NotFoundError(f"Student '{student_id}' was not found.")
        records = session.run(query, student_id=student_id)
        results = []
        for rec in records:
            results.append({
                "scholarshipId": rec["scholarshipId"],
                "SCHOLARSHIPID": rec["scholarshipId"],
                "studentId": rec["studentId"],
                "STUDENTID": rec["studentId"],
                "studentName": rec["studentName"],
                "STUDENTNAME": rec["studentName"],
                "scholarshipType": rec["scholarshipType"],
                "SCHOLARSHIPTYPE": rec["scholarshipType"],
                "amount": rec["amount"],
                "AMOUNT": rec["amount"],
                "applicationId": rec["applicationId"],
                "APPLICATIONID": rec["applicationId"],
                "applicationStatus": rec["applicationStatus"],
                "APPLICATIONSTATUS": rec["applicationStatus"],
            })
        return results


def get_dashboard_summary():
    """Aggregate dashboard KPI metrics from the Neo4j property graph."""
    query = """
        CALL () { MATCH (s:Student) RETURN count(s) AS total_students }
        CALL () { MATCH (sch:Scholarship) RETURN count(sch) AS total_scholarships, coalesce(sum(sch.amount), 0) AS total_scholarship_amount }
        CALL () { MATCH (f:Fee) RETURN coalesce(sum(f.feeAmount), 0) AS total_fees }
        CALL () { MATCH (p:Payment) RETURN coalesce(sum(p.amountPaid), 0) AS total_paid }
        CALL () { MATCH (a:Application {applicationStatus: 'Pending'}) RETURN count(a) AS pending_applications }
        CALL () { MATCH (a:Application {applicationStatus: 'Approved'}) RETURN count(a) AS approved_applications }
        RETURN
            total_students,
            total_scholarships,
            total_scholarship_amount,
            total_fees,
            total_paid,
            total_fees - total_paid AS total_outstanding,
            pending_applications,
            approved_applications
    """
    with get_driver().session(database=get_database_name()) as session:
        rec = session.run(query).single()

    if rec is None:
        return {
            "total_students": 0,
            "total_scholarships": 0,
            "total_scholarship_amount": 0.0,
            "total_fees": 0.0,
            "total_paid": 0.0,
            "total_outstanding": 0.0,
            "pending_applications": 0,
            "approved_applications": 0,
        }

    return {
        "total_students": int(rec["total_students"]),
        "total_scholarships": int(rec["total_scholarships"]),
        "total_scholarship_amount": float(rec["total_scholarship_amount"]),
        "total_fees": float(rec["total_fees"]),
        "total_paid": float(rec["total_paid"]),
        "total_outstanding": float(rec["total_outstanding"]),
        "pending_applications": int(rec["pending_applications"]),
        "approved_applications": int(rec["approved_applications"]),
    }


# ============================================================
# GRAPH VISUALIZATION & EXPLORATION (CYTOSCAPE.JS INTEGRATION)
# ============================================================

LABEL_STYLES = {
    "Student": {"color": "#2563eb", "shape": "ellipse"},
    "Department": {"color": "#7c3aed", "shape": "round-rectangle"},
    "Program": {"color": "#4f46e5", "shape": "round-rectangle"},
    "StudentProfile": {"color": "#0284c7", "shape": "hexagon"},
    "Guardian": {"color": "#0891b2", "shape": "ellipse"},
    "Application": {"color": "#ea580c", "shape": "diamond"},
    "Scholarship": {"color": "#d97706", "shape": "star"},
    "Disbursement": {"color": "#059669", "shape": "triangle"},
    "BankAccount": {"color": "#16a34a", "shape": "tag"},
    "Fee": {"color": "#dc2626", "shape": "rectangle"},
    "Payment": {"color": "#0d9488", "shape": "vee"},
    "PaymentMethod": {"color": "#64748b", "shape": "barrel"},
}


def _format_node_caption(label, props):
    """Generate a clean, informative human-readable label for graph node visualization."""
    if label == "Student":
        return f"{props.get('studentName', 'Student')} ({props.get('studentId', '')})"
    if label == "Department":
        return f"{props.get('deptName', 'Dept')} ({props.get('deptId', '')})"
    if label == "Program":
        return f"{props.get('programName', 'Program')} ({props.get('programId', '')})"
    if label == "Scholarship":
        amt = props.get("amount", 0)
        return f"{props.get('scholarshipType', 'Scholarship')} ₹{amt:,.0f}" if isinstance(amt, (int, float)) else f"{props.get('scholarshipType', 'Scholarship')} ₹{amt}"
    if label == "Fee":
        amt = props.get("feeAmount", 0)
        return f"{props.get('feeType', 'Fee')} ₹{amt:,.0f}" if isinstance(amt, (int, float)) else f"{props.get('feeType', 'Fee')} ₹{amt}"
    if label == "Payment":
        amt = props.get("amountPaid", 0)
        return f"Payment ₹{amt:,.0f}" if isinstance(amt, (int, float)) else f"Payment ₹{amt}"
    if label == "Application":
        return f"App {props.get('applicationId', '')} [{props.get('applicationStatus', '')}]"
    if label == "Disbursement":
        amt = props.get("amount", 0)
        return f"Disburse ₹{amt:,.0f}" if isinstance(amt, (int, float)) else f"Disburse ₹{amt}"
    if label == "BankAccount":
        return f"{props.get('bankName', 'Bank')} #{props.get('accountNo', '')}"
    if label == "PaymentMethod":
        return f"{props.get('methodName', 'Method')}"
    if label == "Guardian":
        return f"{props.get('guardianName', 'Guardian')} ({props.get('relation', '')})"
    if label == "StudentProfile":
        return f"Profile {props.get('studentId', '')}"
    pk_field = NODE_IDENTIFIERS.get(label, "id")
    return f"{label} {props.get(pk_field, '')}"


def get_graph_data(limit=500, label=None, student_id=None, search=None, preset=None):
    """Retrieve graph elements (nodes and edges) formatted for Cytoscape.js or visual graph explorer."""
    try:
        limit = max(1, min(int(limit), 1000))
    except (ValueError, TypeError):
        raise InvalidInputError("Limit must be an integer between 1 and 1000.")

    if label is not None:
        if not isinstance(label, str) or label not in ALLOWED_PROPERTIES:
            raise InvalidInputError(f"Unsupported label filter '{label}'.")

    if student_id is not None:
        if not isinstance(student_id, str) or not student_id.strip():
            raise InvalidInputError("student_id must be a non-empty string.")
        student_id = student_id.strip()

    if search is not None:
        if not isinstance(search, str):
            raise InvalidInputError("search must be a string.")
        search = search.strip()
        if not search:
            search = None

    with get_driver().session(database=get_database_name()) as session:
        if student_id:
            check = session.run("MATCH (s:Student {studentId: $sid}) RETURN s", sid=student_id).single()
            if not check:
                raise NotFoundError(f"Student '{student_id}' was not found.")

            node_query = """
                MATCH (s:Student {studentId: $sid})
                OPTIONAL MATCH path = (s)-[*1..3]-(m)
                WITH s, collect(distinct m) AS related
                UNWIND [s] + related AS n
                RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
            """
            node_records = list(session.run(node_query, sid=student_id, limit=limit))
            allowed_ids = {r["elem_id"] for r in node_records}

            edge_query = """
                MATCH (s:Student {studentId: $sid})
                OPTIONAL MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN DISTINCT elementId(r) AS rel_id, type(r) AS rel_type, properties(r) AS rel_props,
                                elementId(n) AS src_id, elementId(m) AS tgt_id
                LIMIT $limit
            """
            rel_records = list(session.run(edge_query, sid=student_id, ids=list(allowed_ids), limit=limit))

        elif search:
            node_query = """
                MATCH (n)
                WHERE any(k IN keys(properties(n)) WHERE toLower(toString(properties(n)[k])) CONTAINS toLower($search))
                RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
            """
            node_records = list(session.run(node_query, search=search, limit=limit))
            allowed_ids = {r["elem_id"] for r in node_records}

            edge_query = """
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN DISTINCT elementId(r) AS rel_id, type(r) AS rel_type, properties(r) AS rel_props,
                                elementId(n) AS src_id, elementId(m) AS tgt_id
                LIMIT $limit
            """
            rel_records = list(session.run(edge_query, ids=list(allowed_ids), limit=limit))

        elif label:
            node_query = f"""
                MATCH (n:{label})
                RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
            """
            node_records = list(session.run(node_query, limit=limit))
            allowed_ids = {r["elem_id"] for r in node_records}

            edge_query = """
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids OR elementId(m) IN $ids
                RETURN DISTINCT elementId(r) AS rel_id, type(r) AS rel_type, properties(r) AS rel_props,
                                elementId(n) AS src_id, elementId(m) AS tgt_id
                LIMIT $limit
            """
            rel_records = list(session.run(edge_query, ids=list(allowed_ids), limit=limit))

        elif preset:
            if preset in ("student_journey", "student"):
                node_query = """
                    MATCH (s:Student)
                    WHERE s.studentId IN ['S001', 'S002', 'S003', 'S004', 'S005']
                    OPTIONAL MATCH (d:Department)-[:HAS_PROGRAM]->(p:Program)-[:HAS_STUDENT]->(s)
                    OPTIONAL MATCH (s)-[:HAS_PROFILE]->(sp:StudentProfile)
                    OPTIONAL MATCH (s)-[:HAS_GUARDIAN]->(g:Guardian)
                    OPTIONAL MATCH (s)-[:SUBMITTED]->(a:Application)-[:AWARDS]->(sc:Scholarship)
                    OPTIONAL MATCH (s)-[:HAS_FEE]->(f:Fee)-[:HAS_PAYMENT]->(py:Payment)
                    WITH collect(s) + collect(d) + collect(p) + collect(sp) + collect(g) + collect(a) + collect(sc) + collect(f) + collect(py) AS allNodes
                    UNWIND allNodes AS n
                    WITH DISTINCT n WHERE n IS NOT NULL
                    RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                    LIMIT $limit
                """
            elif preset in ("scholarship_lifecycle", "scholarship"):
                node_query = """
                    MATCH (s:Student)-[:SUBMITTED]->(a:Application)-[:AWARDS]->(sc:Scholarship)
                    OPTIONAL MATCH (sc)-[:HAS_DISBURSEMENT]->(ds:Disbursement)-[:TO_ACCOUNT]->(ba:BankAccount)
                    WITH collect(s) + collect(a) + collect(sc) + collect(ds) + collect(ba) AS allNodes
                    UNWIND allNodes AS n
                    WITH DISTINCT n WHERE n IS NOT NULL
                    RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                    LIMIT $limit
                """
            elif preset in ("fee_payment_flow", "fees", "fee"):
                node_query = """
                    MATCH (s:Student)-[:HAS_FEE]->(f:Fee)-[:HAS_PAYMENT]->(py:Payment)-[:PAID_VIA]->(pm:PaymentMethod)
                    WITH collect(s) + collect(f) + collect(py) + collect(pm) AS allNodes
                    UNWIND allNodes AS n
                    WITH DISTINCT n WHERE n IS NOT NULL
                    RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                    LIMIT $limit
                """
            elif preset in ("department_network", "department"):
                node_query = """
                    MATCH (d:Department)-[:HAS_PROGRAM]->(p:Program)-[:HAS_STUDENT]->(s:Student)
                    WITH collect(d) + collect(p) + collect(s) AS allNodes
                    UNWIND allNodes AS n
                    WITH DISTINCT n WHERE n IS NOT NULL
                    RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                    LIMIT $limit
                """
            else:
                node_query = """
                    MATCH (n)
                    RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                    LIMIT $limit
                """
            node_records = list(session.run(node_query, limit=limit))
            allowed_ids = {r["elem_id"] for r in node_records}

            edge_query = """
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN DISTINCT elementId(r) AS rel_id, type(r) AS rel_type, properties(r) AS rel_props,
                                elementId(n) AS src_id, elementId(m) AS tgt_id
                LIMIT $limit
            """
            rel_records = list(session.run(edge_query, ids=list(allowed_ids), limit=limit))

        else:
            node_query = """
                MATCH (n)
                RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
            """
            node_records = list(session.run(node_query, limit=limit))
            allowed_ids = {r["elem_id"] for r in node_records}

            edge_query = """
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN DISTINCT elementId(r) AS rel_id, type(r) AS rel_type, properties(r) AS rel_props,
                                elementId(n) AS src_id, elementId(m) AS tgt_id
                LIMIT $limit
            """
            rel_records = list(session.run(edge_query, ids=list(allowed_ids), limit=limit))

    nodes = []
    node_id_set = set()
    label_counts = {}

    for r in node_records:
        elem_id = r["elem_id"]
        labels = r["labels"] or ["Node"]
        primary_label = labels[0]
        label_counts[primary_label] = label_counts.get(primary_label, 0) + 1

        props = clean_graph_item(dict(r["props"]))
        pk_field = NODE_IDENTIFIERS.get(primary_label)
        pk_val = props.get(pk_field) if pk_field else None
        caption = _format_node_caption(primary_label, props)
        style = LABEL_STYLES.get(primary_label, {"color": "#64748b", "shape": "ellipse"})

        nodes.append({
            "data": {
                "id": elem_id,
                "label": primary_label,
                "labels": labels,
                "name": caption,
                "caption": caption,
                "primaryKey": pk_val,
                "color": style["color"],
                "shape": style["shape"],
                "properties": props,
            }
        })
        node_id_set.add(elem_id)

    edges = []
    type_counts = {}

    for r in rel_records:
        src = r["src_id"]
        tgt = r["tgt_id"]
        if src in node_id_set and tgt in node_id_set:
            rel_type = r["rel_type"]
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
            edges.append({
                "data": {
                    "id": r["rel_id"],
                    "source": src,
                    "target": tgt,
                    "label": rel_type,
                    "type": rel_type,
                    "properties": clean_graph_item(dict(r["rel_props"] or {})),
                }
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_counts_by_label": label_counts,
        "edge_counts_by_type": type_counts,
    }

