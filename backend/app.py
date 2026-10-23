import os
from datetime import timedelta
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS

try:
    from backend.auth import auth_bp, login_required, validate_csrf
except ModuleNotFoundError:
    from auth import auth_bp, login_required, validate_csrf


try:
    from db import get_connection
except ModuleNotFoundError:
    from backend.db import get_connection

try:
    from backend.neo4j_routes import neo4j_bp
except ModuleNotFoundError:
    from neo4j_routes import neo4j_bp

app = Flask(__name__)

# Session security attributes
app.secret_key = os.getenv("FLASK_SECRET_KEY", "scholarship-fee-mgmt-secret-key-2026-da3")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS")
if cors_origins:
    origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
    CORS(app, resources={r"/*": {"origins": origins_list}}, supports_credentials=True)
else:
    CORS(app, supports_credentials=True)

app.register_blueprint(neo4j_bp)
app.register_blueprint(auth_bp)


@app.before_request
def enforce_csrf():
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        if request.path.startswith("/api/auth/login") or request.path.startswith("/api/auth/logout"):
            return
        if not validate_csrf():
            return jsonify({"error": "CSRF verification failed. Missing or invalid token."}), 403


# ============================================================
# HOME / API STATUS & UI ROUTE
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "message": "Scholarship and Fee Management System API is running"
    })


@app.route("/app")
@app.route("/ui")
def serve_ui():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return send_from_directory(repo_root, "index.html")


# ============================================================
# 1. GET ALL STUDENTS
# ============================================================

@app.route("/api/students", methods=["GET"])
def get_students():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.StudentID,
                s.StudentName,
                s.Phone,
                p.ProgramName,
                p.DegreeLevel,
                d.DeptName
            FROM STUDENT s
            JOIN PROGRAM p
                ON s.ProgramID = p.ProgramID
            JOIN DEPARTMENT d
                ON p.DeptID = d.DeptID
            ORDER BY s.StudentID
        """)

        columns = [col[0] for col in cursor.description]

        students = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(students)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 1B. ADD NEW STUDENT
# ============================================================

@app.route("/api/students", methods=["POST"])
@login_required
def add_student():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON data"
        }), 400

    required_fields = [
        "student_id",
        "student_name",
        "phone",
        "program_id"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO STUDENT (
                StudentID,
                StudentName,
                Phone,
                HouseNo,
                Street,
                City,
                PIN,
                ProgramID
            )
            VALUES (
                :student_id,
                :student_name,
                :phone,
                :house_no,
                :street,
                :city,
                :pin,
                :program_id
            )
        """, {
            "student_id": data["student_id"],
            "student_name": data["student_name"],
            "phone": data["phone"],
            "house_no": data.get("house_no"),
            "street": data.get("street"),
            "city": data.get("city"),
            "pin": data.get("pin"),
            "program_id": data["program_id"]
        })

        conn.commit()

        return jsonify({
            "message": "Student added successfully",
            "student_id": data["student_id"]
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({"error": str(e)}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 1C. GET SINGLE STUDENT
# ============================================================

@app.route("/api/students/<student_id>", methods=["GET"])
def get_student(student_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.StudentID,
                s.StudentName,
                s.Phone,
                s.HouseNo,
                s.Street,
                s.City,
                s.PIN,
                s.ProgramID,
                p.ProgramName,
                p.DegreeLevel,
                d.DeptID,
                d.DeptName
            FROM STUDENT s
            JOIN PROGRAM p
                ON s.ProgramID = p.ProgramID
            JOIN DEPARTMENT d
                ON p.DeptID = d.DeptID
            WHERE s.StudentID = :student_id
        """, {
            "student_id": student_id
        })

        row = cursor.fetchone()

        if not row:
            return jsonify({
                "error": "Student not found"
            }), 404

        columns = [col[0] for col in cursor.description]

        student = dict(zip(columns, row))

        return jsonify(student)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 2. GET ALL SCHOLARSHIPS
# ============================================================

@app.route("/api/scholarships", methods=["GET"])
def get_scholarships():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.ScholarshipID,
                s.ApplicationID,
                st.StudentID,
                st.StudentName,
                s.ScholarshipType,
                s.Amount
            FROM SCHOLARSHIP s
            JOIN SCHOLARSHIP_APPLICATION sa
                ON s.ApplicationID = sa.ApplicationID
            JOIN STUDENT st
                ON sa.StudentID = st.StudentID
            ORDER BY s.ScholarshipID
        """)

        columns = [col[0] for col in cursor.description]

        scholarships = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(scholarships)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# 2A. GET ALL SCHOLARSHIP APPLICATIONS
# ============================================================

@app.route("/api/applications", methods=["GET"])
def get_applications():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sa.ApplicationID,
                sa.StudentID,
                st.StudentName,
                sa.ApplicationDate,
                sa.ApplicationStatus
            FROM SCHOLARSHIP_APPLICATION sa
            JOIN STUDENT st
                ON sa.StudentID = st.StudentID
            ORDER BY sa.ApplicationDate DESC
        """)

        columns = [col[0] for col in cursor.description]

        applications = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(applications)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# 2B. SUBMIT SCHOLARSHIP APPLICATION
# ============================================================

@app.route("/api/applications", methods=["POST"])
@login_required
def add_application():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON data"
        }), 400

    required_fields = [
        "application_id",
        "student_id",
        "application_date"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO SCHOLARSHIP_APPLICATION (
                ApplicationID,
                StudentID,
                ApplicationDate,
                ApplicationStatus
            )
            VALUES (
                :application_id,
                :student_id,
                TO_DATE(:application_date, 'YYYY-MM-DD'),
                'Pending'
            )
        """, {
            "application_id": data["application_id"],
            "student_id": data["student_id"],
            "application_date": data["application_date"]
        })

        conn.commit()

        return jsonify({
            "message": "Scholarship application submitted successfully",
            "application_id": data["application_id"],
            "status": "Pending"
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({"error": str(e)}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# 2B. CREATE SCHOLARSHIP
# ============================================================

@app.route("/api/scholarships", methods=["POST"])
@login_required
def add_scholarship():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON data"
        }), 400

    required_fields = [
        "scholarship_id",
        "application_id",
        "scholarship_type",
        "amount"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check whether the application exists
        # and whether it has been approved.
        cursor.execute("""
            SELECT ApplicationStatus
            FROM SCHOLARSHIP_APPLICATION
            WHERE ApplicationID = :application_id
        """, {
            "application_id": data["application_id"]
        })

        application = cursor.fetchone()

        if not application:
            return jsonify({
                "error": "Application not found"
            }), 404

        if application[0] != "Approved":
            return jsonify({
                "error": "Scholarship can only be created for an approved application"
            }), 400

        # Insert scholarship
        cursor.execute("""
            INSERT INTO SCHOLARSHIP (
                ScholarshipID,
                ApplicationID,
                ScholarshipType,
                Amount
            )
            VALUES (
                :scholarship_id,
                :application_id,
                :scholarship_type,
                :amount
            )
        """, {
            "scholarship_id": data["scholarship_id"],
            "application_id": data["application_id"],
            "scholarship_type": data["scholarship_type"],
            "amount": data["amount"]
        })

        conn.commit()

        return jsonify({
            "message": "Scholarship created successfully",
            "scholarship_id": data["scholarship_id"],
            "application_id": data["application_id"],
            "amount": data["amount"]
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 400

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# 2C. GET STUDENT SCHOLARSHIPS
# ============================================================

@app.route("/api/students/<student_id>/scholarships", methods=["GET"])
def get_student_scholarships(student_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sa.ApplicationID,
                sa.ApplicationDate,
                sa.ApplicationStatus,
                s.ScholarshipID,
                s.ScholarshipType,
                s.Amount
            FROM SCHOLARSHIP_APPLICATION sa
            LEFT JOIN SCHOLARSHIP s
                ON sa.ApplicationID = s.ApplicationID
            WHERE sa.StudentID = :student_id
            ORDER BY sa.ApplicationDate DESC
        """, {
            "student_id": student_id
        })

        columns = [col[0] for col in cursor.description]

        scholarships = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(scholarships)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# 2D. UPDATE SCHOLARSHIP APPLICATION STATUS
# ============================================================

@app.route("/api/applications/<application_id>/status", methods=["PUT"])
@login_required
def update_application_status(application_id):
    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({
            "error": "Status is required"
        }), 400

    status = data["status"]

    if status not in ["Pending", "Approved", "Rejected"]:
        return jsonify({
            "error": "Status must be Pending, Approved, or Rejected"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE SCHOLARSHIP_APPLICATION
            SET ApplicationStatus = :status
            WHERE ApplicationID = :application_id
        """, {
            "status": status,
            "application_id": application_id
        })

        if cursor.rowcount == 0:
            conn.rollback()

            return jsonify({
                "error": "Application not found"
            }), 404

        conn.commit()

        return jsonify({
            "message": "Application status updated successfully",
            "application_id": application_id,
            "status": status
        })

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 400

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# 2D. GET ALL DISBURSEMENTS
# ============================================================

@app.route("/api/disbursements", methods=["GET"])
def get_disbursements():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                d.DisbursementID,
                d.ScholarshipID,
                s.ApplicationID,
                sa.StudentID,
                st.StudentName,
                d.AccountNo,
                b.BankName,
                b.IFSC,
                d.DisbursementDate,
                d.Amount,
                d.DisbursementMode
            FROM DISBURSEMENT d
            JOIN SCHOLARSHIP s
                ON d.ScholarshipID = s.ScholarshipID
            JOIN SCHOLARSHIP_APPLICATION sa
                ON s.ApplicationID = sa.ApplicationID
            JOIN STUDENT st
                ON sa.StudentID = st.StudentID
            JOIN BANK_ACCOUNT b
                ON d.AccountNo = b.AccountNo
            ORDER BY d.DisbursementDate DESC
        """)

        columns = [col[0] for col in cursor.description]

        disbursements = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(disbursements)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# 2E. CREATE DISBURSEMENT
# ============================================================

@app.route("/api/disbursements", methods=["POST"])
@login_required
def add_disbursement():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON data"
        }), 400

    required_fields = [
        "disbursement_id",
        "scholarship_id",
        "account_no",
        "disbursement_date",
        "amount",
        "disbursement_mode"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    if data["disbursement_mode"] not in [
        "Bank Transfer",
        "Direct Transfer"
    ]:
        return jsonify({
            "error": "Disbursement mode must be Bank Transfer or Direct Transfer"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check that scholarship exists
        cursor.execute("""
            SELECT ScholarshipID
            FROM SCHOLARSHIP
            WHERE ScholarshipID = :scholarship_id
        """, {
            "scholarship_id": data["scholarship_id"]
        })

        scholarship = cursor.fetchone()

        if not scholarship:
            return jsonify({
                "error": "Scholarship not found"
            }), 404

        # Check that bank account exists
        cursor.execute("""
            SELECT AccountNo
            FROM BANK_ACCOUNT
            WHERE AccountNo = :account_no
        """, {
            "account_no": data["account_no"]
        })

        account = cursor.fetchone()

        if not account:
            return jsonify({
                "error": "Bank account not found"
            }), 404

        # Insert disbursement
        cursor.execute("""
            INSERT INTO DISBURSEMENT (
                DisbursementID,
                ScholarshipID,
                AccountNo,
                DisbursementDate,
                Amount,
                DisbursementMode
            )
            VALUES (
                :disbursement_id,
                :scholarship_id,
                :account_no,
                TO_DATE(:disbursement_date, 'YYYY-MM-DD'),
                :amount,
                :disbursement_mode
            )
        """, {
            "disbursement_id": data["disbursement_id"],
            "scholarship_id": data["scholarship_id"],
            "account_no": data["account_no"],
            "disbursement_date": data["disbursement_date"],
            "amount": data["amount"],
            "disbursement_mode": data["disbursement_mode"]
        })

        conn.commit()

        return jsonify({
            "message": "Disbursement recorded successfully",
            "disbursement_id": data["disbursement_id"],
            "scholarship_id": data["scholarship_id"],
            "account_no": data["account_no"],
            "amount": data["amount"],
            "disbursement_mode": data["disbursement_mode"]
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 400

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# 2F. CREATE STUDENT FEE
# ============================================================

@app.route("/api/fees", methods=["POST"])
@login_required
def add_fee():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON data"
        }), 400

    required_fields = [
        "fee_id",
        "student_id",
        "fee_amount",
        "due_date"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    try:
        fee_amount = float(data["fee_amount"])

        if fee_amount < 0:
            return jsonify({
                "error": "Fee amount cannot be negative"
            }), 400

    except (ValueError, TypeError):
        return jsonify({
            "error": "Fee amount must be a valid number"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check that student exists
        cursor.execute("""
            SELECT StudentID
            FROM STUDENT
            WHERE StudentID = :student_id
        """, {
            "student_id": data["student_id"]
        })

        student = cursor.fetchone()

        if not student:
            return jsonify({
                "error": "Student not found"
            }), 404

        # Insert fee
        cursor.execute("""
            INSERT INTO STUDENT_FEE (
                FeeID,
                StudentID,
                FeeAmount,
                DueDate
            )
            VALUES (
                :fee_id,
                :student_id,
                :fee_amount,
                TO_DATE(:due_date, 'YYYY-MM-DD')
            )
        """, {
            "fee_id": data["fee_id"],
            "student_id": data["student_id"],
            "fee_amount": fee_amount,
            "due_date": data["due_date"]
        })

        conn.commit()

        return jsonify({
            "message": "Student fee created successfully",
            "fee_id": data["fee_id"],
            "student_id": data["student_id"],
            "fee_amount": fee_amount,
            "due_date": data["due_date"]
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 400

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# 3. GET ALL STUDENT FEES
# ============================================================

@app.route("/api/fees", methods=["GET"])
def get_fees():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                f.FeeID,
                f.StudentID,
                s.StudentName,
                f.FeeAmount,
                f.DueDate,
                NVL(SUM(p.AmountPaid), 0) AS AmountPaid,
                f.FeeAmount - NVL(SUM(p.AmountPaid), 0)
                    AS OutstandingAmount
            FROM STUDENT_FEE f
            JOIN STUDENT s
                ON f.StudentID = s.StudentID
            LEFT JOIN FEE_PAYMENT p
                ON f.FeeID = p.FeeID
            GROUP BY
                f.FeeID,
                f.StudentID,
                s.StudentName,
                f.FeeAmount,
                f.DueDate
            ORDER BY f.FeeID
        """)

        columns = [col[0] for col in cursor.description]

        fees = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(fees)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 3B. GET STUDENT FEES
# ============================================================

@app.route("/api/students/<student_id>/fees", methods=["GET"])
def get_student_fees(student_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                f.FeeID,
                f.StudentID,
                s.StudentName,
                f.FeeAmount,
                f.DueDate,
                NVL(SUM(p.AmountPaid), 0) AS AmountPaid,
                f.FeeAmount - NVL(SUM(p.AmountPaid), 0)
                    AS OutstandingAmount
            FROM STUDENT_FEE f
            JOIN STUDENT s
                ON f.StudentID = s.StudentID
            LEFT JOIN FEE_PAYMENT p
                ON f.FeeID = p.FeeID
            WHERE f.StudentID = :student_id
            GROUP BY
                f.FeeID,
                f.StudentID,
                s.StudentName,
                f.FeeAmount,
                f.DueDate
            ORDER BY f.FeeID
        """, {
            "student_id": student_id
        })

        columns = [col[0] for col in cursor.description]

        fees = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(fees)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 4. GET ALL FEE PAYMENTS
# ============================================================

@app.route("/api/payments", methods=["GET"])
def get_payments():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.PaymentID,
                p.FeeID,
                f.StudentID,
                s.StudentName,
                p.ScholarshipID,
                pm.MethodName,
                p.PaymentDate,
                p.AmountPaid,
                p.TransactionID
            FROM FEE_PAYMENT p
            JOIN STUDENT_FEE f
                ON p.FeeID = f.FeeID
            JOIN STUDENT s
                ON f.StudentID = s.StudentID
            JOIN PAYMENT_METHOD pm
                ON p.MethodID = pm.MethodID
            ORDER BY p.PaymentID
        """)

        columns = [col[0] for col in cursor.description]

        payments = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(payments)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 4B. ADD FEE PAYMENT
# ============================================================

@app.route("/api/payments", methods=["POST"])
@login_required
def add_payment():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON data"
        }), 400

    required_fields = [
        "payment_id",
        "fee_id",
        "method_id",
        "payment_date",
        "amount_paid",
        "transaction_id"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO FEE_PAYMENT (
                PaymentID,
                FeeID,
                ScholarshipID,
                MethodID,
                PaymentDate,
                AmountPaid,
                TransactionID
            )
            VALUES (
                :payment_id,
                :fee_id,
                :scholarship_id,
                :method_id,
                TO_DATE(:payment_date, 'YYYY-MM-DD'),
                :amount_paid,
                :transaction_id
            )
        """, {
            "payment_id": data["payment_id"],
            "fee_id": data["fee_id"],
            "scholarship_id": data.get("scholarship_id"),
            "method_id": data["method_id"],
            "payment_date": data["payment_date"],
            "amount_paid": data["amount_paid"],
            "transaction_id": data["transaction_id"]
        })

        conn.commit()

        return jsonify({
            "message": "Fee payment recorded successfully",
            "payment_id": data["payment_id"],
            "transaction_id": data["transaction_id"]
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({"error": str(e)}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 4C. GET STUDENT PAYMENTS
# ============================================================

@app.route("/api/students/<student_id>/payments", methods=["GET"])
def get_student_payments(student_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.PaymentID,
                p.FeeID,
                p.ScholarshipID,
                pm.MethodName,
                p.PaymentDate,
                p.AmountPaid,
                p.TransactionID
            FROM FEE_PAYMENT p
            JOIN STUDENT_FEE f
                ON p.FeeID = f.FeeID
            JOIN PAYMENT_METHOD pm
                ON p.MethodID = pm.MethodID
            WHERE f.StudentID = :student_id
            ORDER BY p.PaymentDate DESC
        """, {
            "student_id": student_id
        })

        columns = [col[0] for col in cursor.description]

        payments = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return jsonify(payments)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# 5. DASHBOARD SUMMARY
# ============================================================

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM STUDENT
        """)
        total_students = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM SCHOLARSHIP
        """)
        total_scholarships = cursor.fetchone()[0]

        cursor.execute("""
            SELECT NVL(SUM(Amount), 0)
            FROM SCHOLARSHIP
        """)
        total_scholarship_amount = cursor.fetchone()[0]

        cursor.execute("""
            SELECT NVL(SUM(FeeAmount), 0)
            FROM STUDENT_FEE
        """)
        total_fees = cursor.fetchone()[0]

        cursor.execute("""
            SELECT NVL(SUM(AmountPaid), 0)
            FROM FEE_PAYMENT
        """)
        total_paid = cursor.fetchone()[0]

        total_outstanding = total_fees - total_paid

        cursor.execute("""
            SELECT COUNT(*)
            FROM SCHOLARSHIP_APPLICATION
            WHERE ApplicationStatus = 'Pending'
        """)
        pending_applications = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM SCHOLARSHIP_APPLICATION
            WHERE ApplicationStatus = 'Approved'
        """)
        approved_applications = cursor.fetchone()[0]

        return jsonify({
            "total_students": total_students,
            "total_scholarships": total_scholarships,
            "total_scholarship_amount": total_scholarship_amount,
            "total_fees": total_fees,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "pending_applications": pending_applications,
            "approved_applications": approved_applications
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# SYSTEM HEALTH & TELEMETRY
# ============================================================

@app.route("/api/health", methods=["GET"])
def system_health():
    """Consolidated system health check and component telemetry."""
    status = {
        "status": "healthy",
        "flask": {
            "status": "healthy",
            "uptime": "active",
            "message": "Scholarship and Fee Management System API is running"
        },
        "oracle": {
            "status": "unavailable",
            "tables": 12,
            "total_records": 0
        },
        "neo4j": {
            "status": "unavailable",
            "total_nodes": 0,
            "total_edges": 0
        }
    }

    # Check Oracle
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        tables = [
            "DEPARTMENT", "PROGRAM", "STUDENT", "STUDENT_PROFILE",
            "GUARDIAN", "SCHOLARSHIP", "SCHOLARSHIP_APPLICATION",
            "STUDENT_FEE", "PAYMENT_METHOD", "FEE_PAYMENT",
            "BANK_ACCOUNT", "DISBURSEMENT"
        ]
        total = 0
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                row = cursor.fetchone()
                if row:
                    total += row[0]
            except Exception:
                pass
        status["oracle"] = {
            "status": "connected",
            "tables": len(tables),
            "total_records": total
        }
    except Exception as e:
        status["oracle"]["error"] = str(e)
        status["status"] = "degraded"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Check Neo4j
    try:
        try:
            from backend.neo4j_db import get_driver
        except (ImportError, ModuleNotFoundError):
            from neo4j_db import get_driver
        driver = get_driver()
        with driver.session() as session:
            r_nodes = session.run("MATCH (n) RETURN count(n) AS cnt")
            node_cnt = r_nodes.single()["cnt"]
            r_edges = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            edge_cnt = r_edges.single()["cnt"]
            status["neo4j"] = {
                "status": "connected",
                "total_nodes": node_cnt,
                "total_edges": edge_cnt
            }
    except Exception as e:
        status["neo4j"]["error"] = str(e)
        status["status"] = "degraded"

    return jsonify(status), 200


# ============================================================
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    port = int(os.getenv("PORT", "5050"))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=debug_mode)
