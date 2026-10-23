"""Flask routes for the Neo4j backend, separate from Oracle routes."""

from flask import Blueprint, jsonify, request
from neo4j.exceptions import Neo4jError

try:
    from backend.neo4j_db import verify_connection
    from backend.graph_service import (
        ConflictError,
        GraphServiceError,
        InvalidInputError,
        NotFoundError,
        create_application,
        create_bank_account,
        create_disbursement,
        create_fee,
        create_node,
        create_payment,
        create_scholarship,
        create_student,
        get_application,
        get_bank_account,
        get_dashboard_summary,
        get_department,
        get_disbursement,
        get_fee,
        get_graph_data,
        get_node,
        get_payment,
        get_program_students,
        get_scholarship,
        get_student,
        get_student_applications,
        get_student_fees,
        get_student_guardians,
        get_student_payments,
        get_student_profile,
        get_student_scholarships,
        list_applications,
        list_bank_accounts,
        list_departments,
        list_disbursements,
        list_fees,
        list_nodes,
        list_payments,
        list_programs,
        list_scholarships,
        list_students,
        update_application_status,
    )
except ModuleNotFoundError:
    from neo4j_db import verify_connection
    from graph_service import (
        ConflictError,
        GraphServiceError,
        InvalidInputError,
        NotFoundError,
        create_application,
        create_bank_account,
        create_disbursement,
        create_fee,
        create_node,
        create_payment,
        create_scholarship,
        create_student,
        get_application,
        get_bank_account,
        get_dashboard_summary,
        get_department,
        get_disbursement,
        get_fee,
        get_graph_data,
        get_node,
        get_payment,
        get_program_students,
        get_scholarship,
        get_student,
        get_student_applications,
        get_student_fees,
        get_student_guardians,
        get_student_payments,
        get_student_profile,
        get_student_scholarships,
        list_applications,
        list_bank_accounts,
        list_departments,
        list_disbursements,
        list_fees,
        list_nodes,
        list_payments,
        list_programs,
        list_scholarships,
        list_students,
        update_application_status,
    )

neo4j_bp = Blueprint("neo4j_api", __name__, url_prefix="/api/neo4j")


# ============================================================
# HEALTH ENDPOINT
# ============================================================


@neo4j_bp.route("/health", methods=["GET"])
def neo4j_health():
    """Report Neo4j availability without exposing connection details."""
    try:
        verify_connection()
        return jsonify({"database": "neo4j", "status": "ok"}), 200
    except (RuntimeError, Neo4jError, OSError):
        return jsonify({
            "database": "neo4j",
            "status": "unavailable",
        }), 503


# ============================================================
# STUDENTS ENDPOINTS
# ============================================================


@neo4j_bp.route("/students", methods=["GET"])
def api_list_students():
    """List students with enrolled program and department details."""
    raw_limit = request.args.get("limit", "100")
    try:
        limit = int(raw_limit)
        students = list_students(limit=limit)
        return jsonify({"students": students, "count": len(students)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve students."}), 500


@neo4j_bp.route("/students/<student_id>", methods=["GET"])
def api_get_student(student_id):
    """Retrieve detailed student information with program and department."""
    try:
        student = get_student(student_id)
        return jsonify({"student": student}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve student."}), 500


@neo4j_bp.route("/students", methods=["POST"])
def api_create_student():
    """Create a new student in the graph database."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    try:
        student = create_student(properties)
        return jsonify({"student": student}), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to create student."}), 500


@neo4j_bp.route("/students/<student_id>/profile", methods=["GET"])
def api_get_student_profile(student_id):
    """Retrieve the student's profile."""
    try:
        profile = get_student_profile(student_id)
        return jsonify({"studentId": student_id, "profile": profile}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve student profile."}), 500


@neo4j_bp.route("/students/<student_id>/guardians", methods=["GET"])
def api_get_student_guardians(student_id):
    """Retrieve guardians associated with a student."""
    try:
        guardians = get_student_guardians(student_id)
        return jsonify({
            "studentId": student_id,
            "guardians": guardians,
            "count": len(guardians),
        }), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve guardians."}), 500


# ============================================================
# DEPARTMENTS & PROGRAMS ENDPOINTS
# ============================================================


@neo4j_bp.route("/departments", methods=["GET"])
def api_list_departments():
    """List all departments with program counts."""
    try:
        departments = list_departments()
        return jsonify({"departments": departments, "count": len(departments)}), 200
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve departments."}), 500


@neo4j_bp.route("/departments/<dept_id>", methods=["GET"])
def api_get_department(dept_id):
    """Retrieve department and its programs."""
    try:
        data = get_department(dept_id)
        return jsonify(data), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve department."}), 500


@neo4j_bp.route("/programs", methods=["GET"])
def api_list_programs():
    """List all programs with department information."""
    try:
        programs = list_programs()
        return jsonify({"programs": programs, "count": len(programs)}), 200
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve programs."}), 500


@neo4j_bp.route("/programs/<program_id>/students", methods=["GET"])
def api_get_program_students(program_id):
    """Retrieve students enrolled in a specific program."""
    try:
        data = get_program_students(program_id)
        return jsonify(data), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve program students."}), 500


# ============================================================
# APPLICATIONS ENDPOINTS
# ============================================================


@neo4j_bp.route("/applications", methods=["GET"])
def api_list_applications():
    """List applications with optional status filter."""
    raw_limit = request.args.get("limit", "100")
    status = request.args.get("status")
    try:
        limit = int(raw_limit)
        applications = list_applications(status=status, limit=limit)
        return jsonify({"applications": applications, "count": len(applications)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve applications."}), 500


@neo4j_bp.route("/applications/<application_id>", methods=["GET"])
def api_get_application(application_id):
    """Retrieve an application by ID along with its student and scholarship."""
    try:
        data = get_application(application_id)
        return jsonify(data), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve application."}), 500


@neo4j_bp.route("/applications", methods=["POST"])
def api_create_application():
    """Create a new application for a student."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    try:
        application = create_application(properties)
        return jsonify({"application": application}), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to create application."}), 500


@neo4j_bp.route("/applications/<application_id>/status", methods=["PUT"])
def api_update_application_status(application_id):
    """Update application status ('Pending', 'Approved', 'Rejected')."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    new_status = payload.get("status") or payload.get("applicationStatus")
    if not new_status:
        return jsonify({"error": "A 'status' or 'applicationStatus' string is required."}), 400

    try:
        application = update_application_status(application_id, new_status)
        return jsonify({"application": application}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to update application status."}), 500


@neo4j_bp.route("/students/<student_id>/applications", methods=["GET"])
def api_get_student_applications(student_id):
    """Retrieve all applications submitted by a specific student."""
    try:
        applications = get_student_applications(student_id)
        return jsonify({
            "studentId": student_id,
            "applications": applications,
            "count": len(applications),
        }), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve student applications."}), 500


# ============================================================
# SCHOLARSHIPS ENDPOINTS
# ============================================================


@neo4j_bp.route("/scholarships", methods=["GET"])
def api_list_scholarships():
    """List scholarships with application and student details."""
    raw_limit = request.args.get("limit", "100")
    try:
        limit = int(raw_limit)
        scholarships = list_scholarships(limit=limit)
        return jsonify({"scholarships": scholarships, "count": len(scholarships)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve scholarships."}), 500


@neo4j_bp.route("/scholarships/<scholarship_id>", methods=["GET"])
def api_get_scholarship(scholarship_id):
    """Retrieve scholarship details, linked application, student, and disbursements."""
    try:
        data = get_scholarship(scholarship_id)
        return jsonify(data), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve scholarship."}), 500


@neo4j_bp.route("/scholarships", methods=["POST"])
def api_create_scholarship():
    """Create a scholarship for an approved application."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    try:
        scholarship = create_scholarship(properties)
        return jsonify({"scholarship": scholarship}), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to create scholarship."}), 500


# ============================================================
# GENERIC NODE CRUD ENDPOINTS (FOUNDATIONAL)
# ============================================================


@neo4j_bp.route("/nodes/<label>", methods=["GET"])
def api_list_nodes(label):
    """List nodes belonging to an allowlisted label."""
    raw_limit = request.args.get("limit", "100")

    try:
        limit = int(raw_limit)
        items = list_nodes(label, limit=limit)
        return jsonify({"items": items, "count": len(items)}), 200
    except (ValueError, InvalidInputError):
        return jsonify({"error": "Invalid label or limit."}), 400
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve graph nodes."}), 500
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503


@neo4j_bp.route("/nodes/<label>/<identifier>", methods=["GET"])
def api_get_node(label, identifier):
    """Retrieve a node by its label and identifier."""
    try:
        item = get_node(label, identifier)
        return jsonify({"item": item}), 200
    except InvalidInputError:
        return jsonify({"error": "Invalid label or identifier."}), 400
    except NotFoundError:
        return jsonify({"error": "Node not found."}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve graph node."}), 500


@neo4j_bp.route("/nodes/<label>", methods=["POST"])
def api_create_node(label):
    """Create an allowlisted node from a JSON object."""
    properties = request.get_json(silent=True)

    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    try:
        item = create_node(label, properties)
        return jsonify({"item": item}), 201
    except InvalidInputError:
        return jsonify({"error": "Invalid label, identifier, or properties."}), 400
    except ConflictError:
        return jsonify({"error": "Node with this identifier already exists."}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to create graph node."}), 500


# ============================================================
# DASHBOARD SUMMARY ENDPOINT
# ============================================================


@neo4j_bp.route("/dashboard", methods=["GET"])
def api_get_dashboard():
    """Retrieve aggregate KPI metrics across the Neo4j graph."""
    try:
        summary = get_dashboard_summary()
        return jsonify(summary), 200
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve dashboard summary."}), 500


# ============================================================
# GRAPH VISUALIZATION ENDPOINT (CYTOSCAPE.JS)
# ============================================================


@neo4j_bp.route("/graph", methods=["GET"])
def api_get_graph():
    """Retrieve full or filtered property graph structure for interactive visualization."""
    limit = request.args.get("limit", 500, type=int)
    label = request.args.get("label")
    student_id = request.args.get("student_id")
    search = request.args.get("search")
    preset = request.args.get("preset")
    try:
        data = get_graph_data(limit=limit, label=label, student_id=student_id, search=search, preset=preset)
        return jsonify(data), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve graph data."}), 500


# ============================================================
# FEES ENDPOINTS
# ============================================================


@neo4j_bp.route("/fees", methods=["GET"])
def api_list_fees():
    """List student fees with amount paid and outstanding balance."""
    raw_limit = request.args.get("limit", "100")
    try:
        limit = int(raw_limit)
        fees = list_fees(limit=limit)
        return jsonify({"fees": fees, "count": len(fees)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve fees."}), 500


@neo4j_bp.route("/fees/<fee_id>", methods=["GET"])
def api_get_fee(fee_id):
    """Retrieve a single fee record by feeId including payment history."""
    try:
        fee = get_fee(fee_id)
        return jsonify({"fee": fee}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve fee record."}), 500


@neo4j_bp.route("/fees", methods=["POST"])
def api_create_fee():
    """Create a new student fee in the graph."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must contain JSON data"}), 400
    try:
        item = create_fee(properties)
        return jsonify({
            "message": "Student fee created successfully",
            "fee": item,
            "fee_id": item["feeId"],
            "student_id": item["studentId"],
            "fee_amount": item["feeAmount"],
            "due_date": item["dueDate"],
        }), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to create fee."}), 500


@neo4j_bp.route("/students/<student_id>/fees", methods=["GET"])
def api_get_student_fees(student_id):
    """Retrieve all fee records for a specific student."""
    try:
        fees = get_student_fees(student_id)
        return jsonify({"fees": fees, "count": len(fees)}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve student fees."}), 500


# ============================================================
# PAYMENTS ENDPOINTS
# ============================================================


@neo4j_bp.route("/payments", methods=["GET"])
def api_list_payments():
    """List all fee payments."""
    raw_limit = request.args.get("limit", "100")
    try:
        limit = int(raw_limit)
        payments = list_payments(limit=limit)
        return jsonify({"payments": payments, "count": len(payments)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve payments."}), 500


@neo4j_bp.route("/payments/<payment_id>", methods=["GET"])
def api_get_payment(payment_id):
    """Retrieve a single payment record by paymentId."""
    try:
        payment = get_payment(payment_id)
        return jsonify({"payment": payment}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve payment record."}), 500


@neo4j_bp.route("/payments", methods=["POST"])
def api_create_payment():
    """Record a new fee payment."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must contain JSON data"}), 400
    try:
        item = create_payment(properties)
        return jsonify({
            "message": "Fee payment recorded successfully",
            "payment": item,
            "payment_id": item["paymentId"],
            "transaction_id": item["transactionId"],
        }), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to record payment."}), 500


@neo4j_bp.route("/students/<student_id>/payments", methods=["GET"])
def api_get_student_payments(student_id):
    """Retrieve all payments made by a specific student."""
    try:
        payments = get_student_payments(student_id)
        return jsonify({"payments": payments, "count": len(payments)}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve student payments."}), 500


# ============================================================
# DISBURSEMENTS ENDPOINTS
# ============================================================


@neo4j_bp.route("/disbursements", methods=["GET"])
def api_list_disbursements():
    """List all scholarship disbursements."""
    raw_limit = request.args.get("limit", "100")
    try:
        limit = int(raw_limit)
        disbursements = list_disbursements(limit=limit)
        return jsonify({"disbursements": disbursements, "count": len(disbursements)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve disbursements."}), 500


@neo4j_bp.route("/disbursements/<disbursement_id>", methods=["GET"])
def api_get_disbursement(disbursement_id):
    """Retrieve a single disbursement record by disbursementId."""
    try:
        disbursement = get_disbursement(disbursement_id)
        return jsonify({"disbursement": disbursement}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve disbursement record."}), 500


@neo4j_bp.route("/disbursements", methods=["POST"])
def api_create_disbursement():
    """Record a new scholarship disbursement."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must contain JSON data"}), 400
    try:
        item = create_disbursement(properties)
        return jsonify({
            "message": "Disbursement recorded successfully.",
            "disbursement": item,
            "disbursement_id": item["disbursementId"],
        }), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to record disbursement."}), 500


# ============================================================
# BANK ACCOUNTS ENDPOINTS
# ============================================================


@neo4j_bp.route("/bank-accounts", methods=["GET"])
def api_list_bank_accounts():
    """List all bank accounts."""
    raw_limit = request.args.get("limit", "100")
    try:
        limit = int(raw_limit)
        accounts = list_bank_accounts(limit=limit)
        return jsonify({"bank_accounts": accounts, "count": len(accounts)}), 200
    except (ValueError, InvalidInputError) as err:
        return jsonify({"error": str(err)}), 400
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve bank accounts."}), 500


@neo4j_bp.route("/bank-accounts/<account_no>", methods=["GET"])
def api_get_bank_account(account_no):
    """Retrieve details for a single bank account."""
    try:
        account = get_bank_account(account_no)
        return jsonify({"bank_account": account}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve bank account."}), 500


@neo4j_bp.route("/bank-accounts", methods=["POST"])
def api_create_bank_account():
    """Create a new bank account in the graph."""
    properties = request.get_json(silent=True)
    if not isinstance(properties, dict):
        return jsonify({"error": "Request body must contain JSON data"}), 400
    try:
        item = create_bank_account(properties)
        return jsonify({
            "message": "Bank account created successfully",
            "bank_account": item,
            "account_no": item["accountNo"],
        }), 201
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except ConflictError as err:
        return jsonify({"error": str(err)}), 409
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to create bank account."}), 500


# ============================================================
# STUDENT SCHOLARSHIPS ENDPOINT
# ============================================================


@neo4j_bp.route("/students/<student_id>/scholarships", methods=["GET"])
def api_get_student_scholarships(student_id):
    """Retrieve all scholarships awarded to a specific student."""
    try:
        scholarships = get_student_scholarships(student_id)
        return jsonify({"scholarships": scholarships, "count": len(scholarships)}), 200
    except InvalidInputError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Neo4jError:
        return jsonify({"error": "Neo4j query failed."}), 503
    except GraphServiceError:
        return jsonify({"error": "Unable to retrieve student scholarships."}), 500

