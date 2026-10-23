# Complete Codebase Analysis & Viva Preparation
# Deliverable 01: Complete Project Inventory

**Project Title:** Scholarship and Fee Management System  
**Audit Status:** Complete File-by-File Line-by-Line Inspection  
**Inspected Source Trees:**  
1. Attached Archive: `/Users/pranjalsingh/Downloads/ScholarshipManagementDA2-main`  
2. Active Workspace: `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System`  

---

## 1. Inventory Summary & File Count

| Functional Category | Attached DA-2 Archive Count | Active Workspace (DA-2 + DA-3) Count | Inspection Status |
| :--- | :--- | :--- | :--- |
| **Frontend** | 1 (`index.html` - 627 lines) | 1 (`index.html` - 2,939 lines) | Fully Inspected |
| **Flask Backend** | 3 (`app.py`, `db.py`, `requirements.txt`) | 5 (`app.py`, `db.py`, `neo4j_db.py`, `graph_service.py`, `neo4j_routes.py`, `requirements.txt`) | Fully Inspected |
| **Oracle Database (SQL/PLSQL)** | 6 (`01_create_tables.sql` to `06_plsql.sql`) | 6 (`01_create_tables.sql` to `06_plsql.sql`) | Fully Inspected |
| **Neo4j Database (Cypher)** | 0 (Absent in DA-2 zip) | 6 (`database/neo4j/01_constraints.cypher` to `06_query_verification.cypher`) | Fully Inspected |
| **Connection & Configuration** | 1 (`.gitignore`) | 4 (`.env.example`, `.env`, `pytest.ini`, `.gitignore`) | Fully Inspected |
| **Automated Tests** | 0 (Absent in DA-2 zip) | 8 (`tests/test_*.py` - 168 tests) | Fully Inspected |
| **Docker & Deployment** | 0 (Absent in DA-2 zip) | 4 (`Dockerfile`, `docker-compose.yml`, `Procfile`, `render.yaml`) | Fully Inspected |
| **Documentation & Reports** | 1 (`README.md` - 739 lines) | 15 (`README.md` + 14 detailed reports in `docs/`) | Fully Inspected |
| **Total Tracked Project Files** | **12 Files** | **42 Files** | **100% Inspected** |

---

## 2. Frontend Files

### 1. `index.html` (Attached Archive Version — DA-2 Milestone)
- **Path:** `/Users/pranjalsingh/Downloads/ScholarshipManagementDA2-main/index.html`
- **Language / File Type:** HTML5, CSS3, Embedded JavaScript (Vanilla ES6+).
- **Line Count:** 627 lines.
- **Purpose:** Standalone single-page frontend prototype for student directory, fee ledger, and scholarship browsing.
- **Key Definitions / Functions:**
  - `loadData(key, defaults)`, `persist()`: Browser `localStorage` abstraction reading/writing `sfms.fixed.students.v1` and `sfms.fixed.fees.v1`.
  - `renderStudents()`, `addStudent()`, `saveStudentEdit()`, `deleteStudent()`: DOM rendering and student state mutations.
  - `renderFeeRecords()`, `addFeeRecord()`, `saveFeeEdit()`, `remainingFor()`, `statusFor()`: Fee ledger management and status calculation.
  - `renderScholarships()`, `renderScholarshipSummary()`: Static catalog rendering of 6 scholarship types.
  - `updateDashboard()`: Computes total students, scholarship students, fee records, and pending payments from local state.
- **Dependencies:** None (zero external CDN libraries, zero API calls).
- **Inspection Status:** **Fully Inspected.**
- **Key Observation:** Line 254 explicitly displays: *"Changes are saved in this browser on this device. This edition works without starting a local backend; its demo data is not shared with other devices."* This file does NOT call the Flask API.

### 2. `index.html` (Active Workspace Version — DA-3 Milestone)
- **Path:** `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/index.html`
- **Language / File Type:** HTML5, CSS3, JavaScript (ES6+), Cytoscape.js canvas, Chart.js.
- **Line Count:** 2,939 lines.
- **Purpose:** Enterprise campus portal featuring animated vector entrance, real-time dual-engine switching (Oracle vs Neo4j), interactive Cytoscape.js graph explorer, and Chart.js financial charts.
- **Key Definitions / Functions:**
  - `fetchAPI(endpoint, options)`: Central asynchronous HTTP wrapper routing requests to `/api` or `/api/neo4j` based on active engine.
  - `initCytoscape()`: Instantiates Cytoscape.js graph canvas, binds node drag/zoom events, layout selection (COSE, Concentric, Breadthfirst, Circle, Grid), and node click inspector.
  - `loadGraphData(params)`: Calls `GET /api/neo4j/graph` with search, label, or student ego-network filters.
  - `initCharts()`, `updateCharts()`: Renders Chart.js responsive charts for financial fee reconciliation and scholarship allocation.
  - `switchEngine(engine)`: Dynamically toggles active backend between Oracle (`/api`) and Neo4j (`/api/neo4j`), updating UI indicators.
  - `loadDashboard()`, `loadStudents()`, `loadScholarships()`, `loadFees()`, `loadPayments()`: Live REST API data fetchers.
- **Dependencies:** Cytoscape.js 3.28.1 (CDN), Chart.js (CDN), Flask backend (`/`, `/api`, `/api/neo4j`).
- **Inspection Status:** **Fully Inspected.**

---

## 3. Flask Backend Files

### 3. `backend/app.py`
- **Path:** `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/backend/app.py` (and `/Users/pranjalsingh/Downloads/ScholarshipManagementDA2-main/backend/app.py`)
- **Language / File Type:** Python 3 (Flask Application).
- **Line Count:** 1,279 lines (DA-2) / 1,308 lines (DA-3).
- **Purpose:** Central WSGI application entry point, Oracle REST route definitions, Blueprint registration, and CORS handler.
- **Key Routes / Definitions:**
  - Blueprint Mounting: `app.register_blueprint(neo4j_bp)` under `/api/neo4j`.
  - Root & UI: `GET /`, `GET /app`, `GET /ui`.
  - Student Endpoints: `GET /api/students`, `POST /api/students`, `GET /api/students/<student_id>`.
  - Scholarship Endpoints: `GET /api/scholarships`, `POST /api/scholarships`, `GET /api/students/<student_id>/scholarships`.
  - Application Endpoints: `GET /api/applications`, `POST /api/applications`, `PUT /api/applications/<application_id>/status`.
  - Disbursement Endpoints: `GET /api/disbursements`, `POST /api/disbursements`.
  - Fee Endpoints: `GET /api/fees`, `POST /api/fees`, `GET /api/students/<student_id>/fees`.
  - Payment Endpoints: `GET /api/payments`, `POST /api/payments`, `GET /api/students/<student_id>/payments`.
  - Dashboard Endpoint: `GET /api/dashboard`.
- **Dependencies:** `flask`, `flask_cors`, `db.py`, `neo4j_routes.py`.
- **Inspection Status:** **Fully Inspected.**

### 4. `backend/db.py`
- **Path:** `backend/db.py` (identical in both directories)
- **Language / File Type:** Python 3.
- **Line Count:** 14 lines.
- **Purpose:** Manages Oracle Database connections using `oracledb`.
- **Key Functions / Variables:**
  - `DB_USER = os.getenv("ORACLE_USER", "system")`
  - `DB_PASSWORD = os.getenv("ORACLE_PASSWORD", "[REDACTED]")`
  - `DB_DSN = os.getenv("ORACLE_DSN", "localhost:1521/FREEPDB1")`
  - `get_connection()`: Calls `oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)`.
- **Dependencies:** `os`, `oracledb`.
- **Inspection Status:** **Fully Inspected.**

### 5. `backend/neo4j_db.py`
- **Path:** `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/backend/neo4j_db.py`
- **Language / File Type:** Python 3.
- **Line Count:** 87 lines.
- **Purpose:** Manages connection pooling, lifecycle, and credential configuration for Neo4j.
- **Key Functions / Variables:**
  - `_load_env_if_needed()`: Searches `.env` in candidate paths if `NEO4J_PASSWORD` is absent.
  - `@lru_cache(maxsize=1) get_driver()`: Creates singleton `GraphDatabase.driver(uri, auth=(username, password))`.
  - `get_database_name()`: Returns `NEO4J_DATABASE` (default `'neo4j'`).
  - `verify_connection()`: Executes `driver.verify_connectivity()` and runs `RETURN 1 AS result`.
  - `close_driver()`: Safely closes driver and evicts cache.
- **Dependencies:** `os`, `functools.lru_cache`, `neo4j.GraphDatabase`, `neo4j.exceptions.Neo4jError`.
- **Inspection Status:** **Fully Inspected.**

### 6. `backend/graph_service.py`
- **Path:** `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/backend/graph_service.py`
- **Language / File Type:** Python 3.
- **Line Count:** 2,219 lines.
- **Purpose:** Complete graph business logic layer, validation, Cypher execution, property whitelisting, and transaction handling.
- **Key Functions / Variables:**
  - Custom Exceptions: `GraphServiceError`, `NotFoundError`, `ConflictError`, `InvalidInputError`.
  - Whitelisting Constants: `ALLOWED_PROPERTIES` (strict per-label attribute whitelist), `NODE_IDENTIFIERS` (canonical PKs).
  - Academic Services: `list_students`, `get_student`, `create_student`, `get_student_profile`, `get_student_guardians`, `list_departments`, `get_department`, `list_programs`, `get_program_students`, `list_applications`, `get_application`, `create_application`, `update_application_status`, `list_scholarships`, `get_scholarship`, `create_scholarship`.
  - Financial Services: `list_fees`, `get_fee`, `get_student_fees`, `create_fee`, `list_payments`, `get_payment`, `get_student_payments`, `create_payment` (enforces overpayment check), `list_disbursements`, `get_disbursement`, `create_disbursement`, `list_bank_accounts`, `get_bank_account`, `create_bank_account`.
  - Analytics & Visualization: `get_dashboard_summary()`, `get_graph_data(limit, label, student_id, search)`.
- **Dependencies:** `neo4j_db.py`, `neo4j.exceptions.Neo4jError`.
- **Inspection Status:** **Fully Inspected.**

### 7. `backend/neo4j_routes.py`
- **Path:** `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/backend/neo4j_routes.py`
- **Language / File Type:** Python 3.
- **Line Count:** 833 lines.
- **Purpose:** Flask Blueprint (`neo4j_bp`, url_prefix `/api/neo4j`) routing incoming HTTP requests to `graph_service.py`.
- **Key Routes (38 Endpoints):**
  - Health: `GET /health`
  - Students: `GET /students`, `GET /students/<id>`, `POST /students`, `GET /students/<id>/profile`, `GET /students/<id>/guardians`, `GET /students/<id>/scholarships`, `GET /students/<id>/fees`, `GET /students/<id>/payments`, `GET /students/<id>/applications`.
  - Departments & Programs: `GET /departments`, `GET /departments/<id>`, `GET /programs`, `GET /programs/<id>/students`.
  - Applications: `GET /applications`, `GET /applications/<id>`, `POST /applications`, `PUT /applications/<id>/status`.
  - Scholarships: `GET /scholarships`, `GET /scholarships/<id>`, `POST /scholarships`.
  - Fees & Payments: `GET /fees`, `GET /fees/<id>`, `POST /fees`, `GET /payments`, `GET /payments/<id>`, `POST /payments`.
  - Disbursements & Bank Accounts: `GET /disbursements`, `GET /disbursements/<id>`, `POST /disbursements`, `GET /bank-accounts`, `GET /bank-accounts/<no>`, `POST /bank-accounts`.
  - Graph & Analytics: `GET /dashboard`, `GET /graph`, `GET /nodes/<label>`, `GET /nodes/<label>/<id>`, `POST /nodes/<label>`.
- **Dependencies:** `flask.Blueprint`, `neo4j_db.py`, `graph_service.py`.
- **Inspection Status:** **Fully Inspected.**

### 8. `backend/requirements.txt`
- **Path:** `backend/requirements.txt`
- **Language / File Type:** Python Pip Requirements.
- **Line Count:** 13 lines (DA-2) / 14 lines (DA-3).
- **Contents:**
  - `Flask==3.1.3`, `flask-cors==6.0.5`, `oracledb==26.0.0`, `neo4j==6.4.1`, `gunicorn==26.2.0`, `Werkzeug==3.1.8`, `Jinja2==3.1.6`, `cryptography==50.0.1`, `click==8.5.0`, `cffi==2.1.1`, `blinker==1.9.0`.
- **Inspection Status:** **Fully Inspected.**

---

## 4. Oracle Database and SQL / PLSQL Files

### 9. `database/01_create_tables.sql`
- **Path:** `database/01_create_tables.sql` (identical in both directories)
- **Language / File Type:** Oracle SQL DDL.
- **Line Count:** 140 lines.
- **Purpose:** Creates the 12 core relational tables and foreign keys.
- **Tables Created:** `DEPARTMENT`, `PROGRAM`, `STUDENT`, `STUDENT_PROFILE`, `GUARDIAN`, `SCHOLARSHIP_APPLICATION`, `SCHOLARSHIP`, `BANK_ACCOUNT`, `DISBURSEMENT`, `STUDENT_FEE`, `PAYMENT_METHOD`, `FEE_PAYMENT`.
- **Inspection Status:** **Fully Inspected.**

### 10. `database/02_constraints.sql`
- **Path:** `database/02_constraints.sql` (identical in both directories)
- **Language / File Type:** Oracle SQL DDL (`ALTER TABLE ADD CONSTRAINT`).
- **Line Count:** 18 lines.
- **Purpose:** Adds business-rule check and unique constraints.
- **Constraints Added:**
  - `chk_application_status`: `ApplicationStatus IN ('Pending', 'Approved', 'Rejected')`
  - `chk_fee_due_date`: `DueDate IS NOT NULL`
  - `chk_disbursement_mode`: `DisbursementMode IN ('Bank Transfer', 'Direct Transfer')`
  - `uq_payment_method_name`: `UNIQUE (MethodName)`
- **Inspection Status:** **Fully Inspected.**

### 11. `database/03_sample_data.sql`
- **Path:** `database/03_sample_data.sql` (identical in both directories)
- **Language / File Type:** Oracle SQL DML (`INSERT INTO`).
- **Line Count:** 286 lines.
- **Purpose:** Seeds initial sample dataset: 3 departments, 3 programs, 5 students, 5 profiles, 5 guardians, 5 applications, 5 scholarships, 5 bank accounts, 4 disbursements, 5 student fees, 4 payment methods, 5 fee payments.
- **Inspection Status:** **Fully Inspected.**

### 12. `database/04_queries.sql`
- **Path:** `database/04_queries.sql` (identical in both directories)
- **Language / File Type:** Oracle SQL DQL (`SELECT`).
- **Line Count:** 318 lines.
- **Purpose:** Contains 20 production SQL queries covering student enrollment, academic reporting, scholarship approvals, fee analysis, outstanding balances, and disbursement auditing.
- **Inspection Status:** **Fully Inspected.**

### 13. `database/05_views.sql`
- **Path:** `database/05_views.sql` (identical in both directories)
- **Language / File Type:** Oracle SQL DDL (`CREATE OR REPLACE VIEW`).
- **Line Count:** 106 lines.
- **Purpose:** Creates 5 database views: `VW_STUDENT_ACADEMIC`, `VW_SCHOLARSHIP_APPLICATION`, `VW_STUDENT_FEE_SUMMARY`, `VW_DISBURSEMENT_DETAILS`, `VW_PENDING_APPLICATIONS`.
- **Inspection Status:** **Fully Inspected.**

### 14. `database/06_plsql.sql`
- **Path:** `database/06_plsql.sql` (identical in both directories)
- **Language / File Type:** Oracle PL/SQL.
- **Line Count:** 218 lines.
- **Purpose:** Implements stored procedures, a stored function, an overpayment prevention trigger, and anonymous demonstration blocks.
- **Constructs Defined:**
  - `P_STUDENT_FEE_STATUS(p_student_id)`: Stored procedure.
  - `F_OUTSTANDING_FEE(p_fee_id)`: Stored function returning numeric balance.
  - `P_APPROVED_SCHOLARSHIPS`: Stored procedure with explicit cursor FOR loop.
  - `TRG_CHECK_FEE_PAYMENT`: BEFORE INSERT FOR EACH ROW trigger on `FEE_PAYMENT`.
  - P5, P6, P7: Anonymous PL/SQL test blocks.
- **Inspection Status:** **Fully Inspected.**

---

## 5. Neo4j Database and Cypher Files

*(Located in `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/database/neo4j/`)*

### 15. `database/neo4j/01_constraints.cypher`
- **Language / File Type:** Cypher DDL.
- **Line Count:** 56 lines.
- **Purpose:** Defines 12 uniqueness constraints (`CREATE CONSTRAINT ... REQUIRE n.<pk> IS UNIQUE`) across all 12 canonical node labels.
- **Inspection Status:** **Fully Inspected.**

### 16. `database/neo4j/02_import_data.cypher`
- **Language / File Type:** Cypher DML (`UNWIND ... MERGE ... SET`).
- **Line Count:** 164 lines.
- **Purpose:** Idempotently imports all baseline entities from DA-2 sample data into Neo4j nodes.
- **Inspection Status:** **Fully Inspected.**

### 17. `database/neo4j/03_create_relationships.cypher`
- **Language / File Type:** Cypher DML (`MATCH ... WHERE ... MERGE (a)-[:TYPE]->(b)`).
- **Line Count:** 66 lines.
- **Purpose:** Traverses foreign key attributes and materializes physical directed relationships across all 12 relationship types.
- **Inspection Status:** **Fully Inspected.**

### 18. `database/neo4j/04_verify_graph.cypher`
- **Language / File Type:** Cypher DQL.
- **Line Count:** 95 lines.
- **Purpose:** Verification suite asserting exact node counts (54 nodes) and relationship counts (55 edges), checking for orphan nodes or dangling foreign keys.
- **Inspection Status:** **Fully Inspected.**

### 19. `database/neo4j/05_graph_queries.cypher`
- **Language / File Type:** Cypher DQL.
- **Line Count:** 103 lines.
- **Purpose:** Advanced graph traversals: Student scholarship journey (5 hops), department-wise exploration, and financial reconciliation using `CALL { ... }` subqueries to avoid Cartesian multiplication.
- **Inspection Status:** **Fully Inspected.**

### 20. `database/neo4j/06_query_verification.cypher`
- **Language / File Type:** Cypher DQL.
- **Line Count:** 108 lines.
- **Purpose:** Financial and business verification queries (pending applications, unlinked scholarships, outstanding fee totals, and cross-product baseline checks).
- **Inspection Status:** **Fully Inspected.**

---

## 6. Tests and Verification Files

*(Located in `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/tests/`)*

### 21. `tests/test_academic_routes.py` (25 Tests)
- **Purpose:** Unit tests for Flask academic endpoints (`/api/neo4j/students`, `/applications`, `/scholarships`, `/departments`, `/programs`).
- **Inspection Status:** **Fully Inspected (25/25 Passing).**

### 22. `tests/test_academic_service.py` (29 Tests)
- **Purpose:** Unit tests for academic business logic in `graph_service.py` (input validation, duplicate handling, relationship wiring).
- **Inspection Status:** **Fully Inspected (29/29 Passing).**

### 23. `tests/test_app_integration.py` (3 Tests)
- **Purpose:** Tests Flask application setup, verifying root endpoint `/`, registration of `neo4j_bp`, and preservation of all 19 original Oracle routes.
- **Inspection Status:** **Fully Inspected (3/3 Passing).**

### 24. `tests/test_financial_routes.py` (26 Tests)
- **Purpose:** Unit tests for Flask financial endpoints (`/api/neo4j/fees`, `/payments`, `/disbursements`, `/bank-accounts`).
- **Inspection Status:** **Fully Inspected (26/26 Passing).**

### 25. `tests/test_financial_service.py` (26 Tests)
- **Purpose:** Unit tests for financial domain rules, overpayment prevention, disbursement limits, and fee balance calculation.
- **Inspection Status:** **Fully Inspected (26/26 Passing).**

### 26. `tests/test_graph_service.py` (27 Tests)
- **Purpose:** Tests core graph utilities, property whitelisting (`ALLOWED_PROPERTIES`), Cypher parameterization, and `get_graph_data()`.
- **Inspection Status:** **Fully Inspected (27/27 Passing).**

### 27. `tests/test_neo4j_live.py` (4 Tests)
- **Purpose:** Live integration tests executed directly against running Docker container `scholarship-neo4j`. Uses UUID-isolated fixtures and self-cleaning teardown.
- **Inspection Status:** **Fully Inspected (4/4 Passing).**

### 28. `tests/test_neo4j_routes.py` (28 Tests)
- **Purpose:** Tests generic node CRUD endpoints, error mapping (400, 404, 409, 503), and Cytoscape graph payload delivery.
- **Inspection Status:** **Fully Inspected (28/28 Passing).**

---

## 7. Docker, Deployment & Configuration Files

### 29. `Dockerfile`
- **Path:** `Dockerfile` (in Active Workspace)
- **Line Count:** 35 lines.
- **Purpose:** Multi-stage production container build (Python 3.12-slim builder -> runner), creates unprivileged `appuser`, exposes port 5000, starts Gunicorn WSGI.
- **Inspection Status:** **Fully Inspected.**

### 30. `docker-compose.yml`
- **Path:** `docker-compose.yml` (in Active Workspace)
- **Line Count:** 42 lines.
- **Purpose:** Orchestrates multi-container local stack: `scholarship-neo4j` (Neo4j 5.26 Community with APOC, healthcheck) and `scholarship-backend` (Flask + Gunicorn), with persistent named volumes.
- **Inspection Status:** **Fully Inspected.**

### 31. `Procfile` & `render.yaml`
- **Purpose:** Deployment manifests for Heroku and Render cloud platforms.
- **Inspection Status:** **Fully Inspected.**

### 32. `pytest.ini`, `.env.example`, `.env`, `.gitignore`
- **Purpose:** Test runner configuration (`testpaths = tests`), environment variable templates, and Git exclusion rules.
- **Inspection Status:** **Fully Inspected.**

---

## 8. Documentation Files

### 33. `README.md`
- **Path:** `README.md` (739 lines in DA-2 zip, 739 lines in Active Workspace)
- **Purpose:** Comprehensive DA-2 submission report detailing team roles, 12 tables, 20 queries, 5 views, PL/SQL units, 18 REST endpoints, and Docker Oracle instructions.
- **Inspection Status:** **Fully Inspected.**

### 34–42. Technical Architectural Reports in `docs/`
- `da3_deployment_guide.md` (Deployment walkthrough)
- `da3_final_completion_report.md` (Final completion signoff)
- `da3_graph_schema.md` (Neo4j graph schema specifications)
- `da3_integration_report.md` (Frontend-backend integration evidence)
- `da3_integration_test_plan.md` (Test strategy & test matrix)
- `da3_member2_final_audit_report.md` (Deep codebase audit)
- `da3_oracle_vs_neo4j.md` (Paradigmatic academic evaluation: Oracle vs Neo4j vs MongoDB)
- `da3_traceability_matrix.md` (Requirement-to-code traceability matrix)
- `member2_api_contract.md` (Formal REST API contract for all 38 Neo4j endpoints)
- `member2_backend_handoff.md`, `member2_completion_report.md`, `member2_schema_contract.md`, `member2_waiting_period_audit.md`, `neo4j_backend.md`.
- **Inspection Status:** **All 14 documents Fully Inspected.**
