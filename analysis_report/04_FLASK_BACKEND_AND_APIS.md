# Complete Codebase Analysis & Viva Preparation
# Deliverable 04: Flask Backend and REST APIs

**Project Title:** Scholarship and Fee Management System  
**Framework:** Flask 3.1.3 (Python WSGI)  
**Modules Audited:** `backend/app.py`, `backend/db.py`, `backend/neo4j_db.py`, `backend/graph_service.py`, `backend/neo4j_routes.py`  
**Total Registered Routes:** **59 Routes** (3 Root/UI + 18 Oracle REST + 38 Neo4j REST)  
**Evidence Level:** `[VERIFIED]` directly from source code and passing automated tests.

---

## 1. Complete API Route Catalog

The following tables document every single verified endpoint across both database engines.

### A. Root and Static UI Routes (`backend/app.py`)

| Method & Endpoint | Handler Function | Purpose | Input | Validation | Database Operation | Response | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /` | `home()` | Health / Status check | None | None | None | `{"message": "Scholarship and Fee Management System API is running"}` | None |
| `GET /app` | `serve_ui()` | Serves frontend SPA | None | None | File read (`index.html`) | Full HTML/CSS/JS document | 404 (if file missing) |
| `GET /ui` | `serve_ui()` | Alternate frontend alias | None | None | File read (`index.html`) | Full HTML/CSS/JS document | 404 (if file missing) |

---

### B. Oracle REST API Endpoints (`backend/app.py` — Prefix `/api`)

| Method & Endpoint | Handler Function | Purpose | Input | Validation | Database Operation | Response | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /api/students` | `get_students()` | Lists all students with academic enrollment | None | None | `SELECT` joining `STUDENT`, `PROGRAM`, `DEPARTMENT` | Array of student objects | 500 (DB failure) |
| `POST /api/students` | `add_student()` | Registers a new student | JSON: `student_id`, `student_name`, `phone`, `program_id`, optional address | Checks mandatory fields | `INSERT INTO STUDENT` with bind params; `conn.commit()` | `{"message": "...", "student_id": "..."}` | 400 (Missing fields / DB error) |
| `GET /api/students/<student_id>` | `get_student(student_id)` | Fetches single student record | URL param: `student_id` | None | `SELECT` from `STUDENT` where `StudentID = :student_id` | Single student object | 404 (Not found), 500 |
| `GET /api/scholarships` | `get_scholarships()` | Lists all awarded scholarships | None | None | `SELECT` joining `SCHOLARSHIP`, `SCHOLARSHIP_APPLICATION`, `STUDENT` | Array of scholarship objects | 500 |
| `POST /api/scholarships` | `add_scholarship()` | Awards scholarship to application | JSON: `scholarship_id`, `application_id`, `scholarship_type`, `amount` | Verifies application exists AND status is `'Approved'` | Checks `SCHOLARSHIP_APPLICATION.ApplicationStatus`; `INSERT INTO SCHOLARSHIP` | `{"message": "...", "scholarship_id": "..."}` | 400 (Not approved / missing), 404 |
| `GET /api/applications` | `get_applications()` | Lists all scholarship applications | None | None | `SELECT` joining `SCHOLARSHIP_APPLICATION`, `STUDENT` | Array of applications | 500 |
| `POST /api/applications` | `add_application()` | Submits a new scholarship application | JSON: `application_id`, `student_id`, `application_date` | Checks required fields | `INSERT INTO SCHOLARSHIP_APPLICATION` with status `'Pending'` | `{"message": "...", "status": "Pending"}` | 400 |
| `PUT /api/applications/<id>/status` | `update_application_status(id)` | Updates application review status | JSON: `status` (`Pending`, `Approved`, `Rejected`) | Must be one of 3 allowed statuses | `UPDATE SCHOLARSHIP_APPLICATION SET ApplicationStatus = :status` | `{"message": "...", "status": "..."}` | 400, 404 (Not found) |
| `GET /api/students/<id>/scholarships` | `get_student_scholarships(id)` | Fetches scholarships for a student | URL param: `id` | None | `SELECT` from `SCHOLARSHIP_APPLICATION` `LEFT JOIN SCHOLARSHIP` | Array of student scholarships | 500 |
| `GET /api/disbursements` | `get_disbursements()` | Lists all scholarship disbursements | None | None | `SELECT` joining `DISBURSEMENT`, `SCHOLARSHIP`, `BANK_ACCOUNT`, `STUDENT` | Array of disbursement details | 500 |
| `POST /api/disbursements` | `add_disbursement()` | Disburses scholarship funds to bank | JSON: `disbursement_id`, `scholarship_id`, `account_no`, `date`, `amount`, `mode` | Mode must be `'Bank Transfer'` or `'Direct Transfer'` | Checks scholarship & bank exist; `INSERT INTO DISBURSEMENT` | `{"message": "...", "disbursement_id": "..."}` | 400, 404 (Scholarship/Bank missing) |
| `GET /api/fees` | `get_fees()` | Lists all fees with balances | None | None | `SELECT` from `STUDENT_FEE` `LEFT JOIN FEE_PAYMENT` with `SUM(AmountPaid)` | Array of fee ledgers with `OutstandingAmount` | 500 |
| `POST /api/fees` | `add_fee()` | Creates tuition fee invoice | JSON: `fee_id`, `student_id`, `fee_amount`, `due_date` | Fee amount must be non-negative numeric | Checks student exists; `INSERT INTO STUDENT_FEE` | `{"message": "...", "fee_id": "..."}` | 400, 404 (Student missing) |
| `GET /api/students/<id>/fees` | `get_student_fees(id)` | Fees for specific student | URL param: `id` | None | `SELECT` fees filtered by `f.StudentID = :student_id` | Array of student fee objects | 500 |
| `GET /api/payments` | `get_payments()` | Lists all fee payments | None | None | `SELECT` joining `FEE_PAYMENT`, `STUDENT_FEE`, `STUDENT`, `PAYMENT_METHOD` | Array of payment transactions | 500 |
| `POST /api/payments` | `add_payment()` | Records a fee payment | JSON: `payment_id`, `fee_id`, `method_id`, `date`, `amount_paid`, `transaction_id`, optional `scholarship_id` | Required fields present | `INSERT INTO FEE_PAYMENT`. Fires Oracle Trigger `TRG_CHECK_FEE_PAYMENT` | `{"message": "...", "payment_id": "..."}` | 400 (Trigger exception / overpayment) |
| `GET /api/students/<id>/payments` | `get_student_payments(id)` | Payments made by student | URL param: `id` | None | `SELECT` joining `FEE_PAYMENT` and `STUDENT_FEE` on `StudentID = :id` | Array of student payments | 500 |
| `GET /api/dashboard` | `get_dashboard()` | System-wide statistics | None | None | Multiple `COUNT(*)` and `NVL(SUM(...), 0)` queries on students, fees, payments, applications | Summary object (total students, fees, paid, dues, apps) | 500 |

---

### C. Neo4j REST API Endpoints (`backend/neo4j_routes.py` — Prefix `/api/neo4j`)

| Method & Endpoint | Handler Function | Purpose | Input / Filters | Validation & Logic | Cypher / Graph Service Operation | Response | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /api/neo4j/health` | `neo4j_health()` | Connection health check | None | Executes `RETURN 1` | `verify_connection()` | `{"database": "neo4j", "status": "ok"}` | 503 (Unavailable) |
| `GET /api/neo4j/students` | `api_list_students()` | List students with programs | Query: `?limit=100` | Validates limit | `MATCH (s:Student)-[:ENROLLED_IN]->(p:Program)` | `{"students": [...], "count": N}` | 400, 500, 503 |
| `GET /api/neo4j/students/<id>` | `api_get_student(id)` | Fetch single student | URL param: `id` | Non-empty check | `MATCH (s:Student {studentId: $id})` | `{"student": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/students` | `api_create_student()` | Create student and enroll in program | JSON: `studentId`, `studentName`, `phone`, `programId`, etc. | Property whitelisting | `create_student()`: merges student and creates `[:HAS_STUDENT]` | `{"message": "...", "student": {...}}` | 400, 404 (Program missing), 409 |
| `GET /api/neo4j/students/<id>/profile` | `api_get_student_profile(id)` | Fetch demographic profile | URL param: `id` | Non-empty check | `MATCH (s:Student)-[:HAS_PROFILE]->(p)` | `{"profile": {...}}` | 400, 404, 503 |
| `GET /api/neo4j/students/<id>/guardians` | `api_get_student_guardians(id)`| Fetch student guardians | URL param: `id` | Non-empty check | `MATCH (s:Student)-[:HAS_GUARDIAN]->(g)` | `{"guardians": [...], "count": N}` | 400, 404, 503 |
| `GET /api/neo4j/departments` | `api_list_departments()` | List all departments | None | None | `MATCH (d:Department)` | `{"departments": [...]}` | 500, 503 |
| `GET /api/neo4j/departments/<id>` | `api_get_department(id)` | Single department details | URL param: `id` | Non-empty check | `MATCH (d:Department {deptId: $id})` | `{"department": {...}}` | 400, 404, 503 |
| `GET /api/neo4j/programs` | `api_list_programs()` | List all degree programs | None | None | `MATCH (p:Program)` | `{"programs": [...]}` | 500, 503 |
| `GET /api/neo4j/programs/<id>/students` | `api_get_program_students(id)`| Students enrolled in program | URL param: `id` | Non-empty check | `MATCH (p:Program {programId: $id})-[:HAS_STUDENT]->(s)` | `{"students": [...], "count": N}` | 400, 404, 503 |
| `GET /api/neo4j/applications` | `api_list_applications()` | List scholarship applications | Query: `?status=Pending` | Status filter validation | `MATCH (s:Student)-[:SUBMITTED]->(a:Application)` | `{"applications": [...]}` | 400, 500, 503 |
| `GET /api/neo4j/applications/<id>` | `api_get_application(id)` | Single application | URL param: `id` | Non-empty check | `MATCH (a:Application {applicationId: $id})` | `{"application": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/applications` | `api_create_application()` | Submit new application | JSON: `applicationId`, `studentId`, `applicationDate` | Status defaults to `'Pending'` | `MATCH (s:Student) CREATE (a:Application) MERGE (s)-[:SUBMITTED]->(a)` | `{"message": "...", "application": {...}}` | 400, 404 (Student missing), 409 |
| `PUT /api/neo4j/applications/<id>/status`| `api_update_application_status(id)`| Approve/Reject application | JSON: `status` | Must be `Pending`, `Approved`, or `Rejected` | `MATCH (a:Application {applicationId: $id}) SET a.applicationStatus = $status` | `{"message": "...", "status": "..."}` | 400, 404, 503 |
| `GET /api/neo4j/students/<id>/applications`| `api_get_student_applications(id)`| Applications by student | URL param: `id` | Non-empty check | `MATCH (s:Student {studentId: $id})-[:SUBMITTED]->(a)` | `{"applications": [...]}` | 400, 404, 503 |
| `GET /api/neo4j/scholarships` | `api_list_scholarships()` | List awarded scholarships | Query: `?limit=100` | Limit check | `MATCH (a:Application)-[:AWARDS]->(sch:Scholarship)` | `{"scholarships": [...]}` | 400, 500, 503 |
| `GET /api/neo4j/scholarships/<id>` | `api_get_scholarship(id)` | Single scholarship details | URL param: `id` | Non-empty check | `MATCH (sch:Scholarship {scholarshipId: $id})` | `{"scholarship": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/scholarships` | `api_create_scholarship()` | Award scholarship | JSON: `scholarshipId`, `applicationId`, `scholarshipType`, `amount` | Enforces application status == `'Approved'` & single award | `create_scholarship()`: checks status, creates node, links `(a)-[:AWARDS]->(sch)` | `{"message": "...", "scholarship": {...}}` | 400 (Not approved), 404, 409 |
| `GET /api/neo4j/fees` | `api_list_fees()` | List all student fees | Query: `?limit=100` | Limit check | `MATCH (s:Student)-[:HAS_FEE]->(f:Fee)` with subquery `sum(p.amountPaid)` | `{"fees": [...]}` with outstanding balances | 400, 500, 503 |
| `GET /api/neo4j/fees/<id>` | `api_get_fee(id)` | Single fee details | URL param: `id` | Non-empty check | `MATCH (f:Fee {feeId: $id})` with payment rollup | `{"fee": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/fees` | `api_create_fee()` | Create fee invoice | JSON: `feeId`, `studentId`, `feeAmount`, `dueDate` | Non-negative amount | Checks student exists; creates `(s)-[:HAS_FEE]->(f)` | `{"message": "...", "fee": {...}}` | 400, 404, 409 |
| `GET /api/neo4j/students/<id>/fees` | `api_get_student_fees(id)` | Fees for single student | URL param: `id` | Non-empty check | `MATCH (s:Student {studentId: $id})-[:HAS_FEE]->(f:Fee)` | `{"fees": [...]}` | 400, 404, 503 |
| `GET /api/neo4j/payments` | `api_list_payments()` | List all fee payments | Query: `?limit=100` | Limit check | `MATCH (f:Fee)-[:HAS_PAYMENT]->(p:Payment)-[:PAID_VIA]->(m)` | `{"payments": [...]}` | 400, 500, 503 |
| `GET /api/neo4j/payments/<id>` | `api_get_payment(id)` | Single payment details | URL param: `id` | Non-empty check | `MATCH (p:Payment {paymentId: $id})` | `{"payment": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/payments` | `api_create_payment()` | Record fee payment | JSON: `paymentId`, `feeId`, `methodId`, `amountPaid`, `transactionId`, `paymentDate` | **Strict Overpayment Check:** `total_paid + amountPaid > total_fee` rejected | `create_payment()` transaction: creates `(:Payment)` and links to Fee & Method | `{"message": "...", "payment": {...}}` | 400 (Overpayment / missing), 404, 409 |
| `GET /api/neo4j/students/<id>/payments`| `api_get_student_payments(id)`| Payments by student | URL param: `id` | Non-empty check | Traverses `(s)-[:HAS_FEE]->(:Fee)-[:HAS_PAYMENT]->(p)` | `{"payments": [...]}` | 400, 404, 503 |
| `GET /api/neo4j/disbursements` | `api_list_disbursements()` | List all disbursements | Query: `?limit=100` | Limit check | Traverses `(sch)-[:HAS_DISBURSEMENT]->(d)-[:TO_ACCOUNT]->(b)` | `{"disbursements": [...]}` | 400, 500, 503 |
| `GET /api/neo4j/disbursements/<id>` | `api_get_disbursement(id)` | Single disbursement | URL param: `id` | Non-empty check | `MATCH (d:Disbursement {disbursementId: $id})` | `{"disbursement": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/disbursements` | `api_create_disbursement()` | Record fund disbursement | JSON: `disbursementId`, `scholarshipId`, `accountNo`, `amount`, `disbursementMode`, `date` | Mode validation + cumulative disbursement limit check | Creates `(:Disbursement)` and links to Scholarship & Account | `{"message": "...", "disbursement": {...}}` | 400 (Limit exceeded / mode), 404, 409 |
| `GET /api/neo4j/bank-accounts` | `api_list_bank_accounts()` | List bank accounts | Query: `?limit=100` | Limit check | `MATCH (b:BankAccount)` | `{"bank_accounts": [...]}` | 400, 500, 503 |
| `GET /api/neo4j/bank-accounts/<no>` | `api_get_bank_account(no)` | Single bank account | URL param: `no` | Non-empty check | `MATCH (b:BankAccount {accountNo: $no})` | `{"bank_account": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/bank-accounts` | `api_create_bank_account()` | Add bank account | JSON: `accountNo`, `bankName`, `ifsc`, `accountType` | Property whitelisting | Creates `(:BankAccount)` node | `{"message": "...", "bank_account": {...}}` | 400, 409 |
| `GET /api/neo4j/students/<id>/scholarships`| `api_get_student_scholarships(id)`| Student scholarships | URL param: `id` | Non-empty check | `MATCH (s:Student {studentId: $id})-[:SUBMITTED]->(a)-[:AWARDS]->(sch)` | `{"scholarships": [...]}` | 400, 404, 503 |
| `GET /api/neo4j/dashboard` | `api_get_dashboard_summary()` | System KPI summary | None | None | `CALL { MATCH ... }` subqueries for total students, fees, paid, apps | Summary object (dual camelCase + UPPERCASE) | 500, 503 |
| `GET /api/neo4j/graph` | `api_get_graph_data()` | Cytoscape graph payload | Query: `?limit=500&label=...&student_id=...&search=...` | Validates label/search/limit | Dynamic Cypher (ego-network `[*1..3]` or full graph) serializing elements | `{"elements": {"nodes": [...], "edges": [...]}}` | 400, 500, 503 |
| `GET /api/neo4j/nodes/<label>` | `api_list_nodes(label)` | Generic node catalog | URL param: `label`, Query: `?limit=100` | Label must be in whitelist | `MATCH (n:<label>) LIMIT $limit` | `{"nodes": [...]}` | 400, 500, 503 |
| `GET /api/neo4j/nodes/<label>/<id>` | `api_get_node(label, id)` | Single generic node | URL params: `label`, `id` | Label & identifier validation | `MATCH (n:<label> {<pk>: $id})` | `{"node": {...}}` | 400, 404, 503 |
| `POST /api/neo4j/nodes/<label>` | `api_create_node(label)` | Generic node ingestion | URL param: `label`, JSON body | Strict `ALLOWED_PROPERTIES` check, rejects nested dicts | `CREATE (n:<label> $props)` | `{"message": "...", "node": {...}}` | 400, 409 (Constraint error) |

---

## 2. Ten Key Workflow Call Chains

### Workflow 1: Fetching Students (`GET /api/students`)
1. User clicks **Students** tab in `index.html`.
2. Frontend executes `fetchAPI('/api/students')`.
3. In `backend/app.py`, `get_students()` is invoked.
4. `db.get_connection()` connects to Oracle `FREEPDB1`.
5. Cursor executes:
   ```sql
   SELECT s.StudentID, s.StudentName, s.Phone, p.ProgramName, p.DegreeLevel, d.DeptName
   FROM STUDENT s
   JOIN PROGRAM p ON s.ProgramID = p.ProgramID
   JOIN DEPARTMENT d ON p.DeptID = d.DeptID
   ORDER BY s.StudentID
   ```
6. Cursor fetches tuples; `dict(zip(columns, row))` constructs JSON array.
7. Flask returns HTTP 200 with student records.
8. Frontend renders table rows in `#studentTableBody`.

### Workflow 2: Creating a Student (`POST /api/students`)
1. User completes "Add New Student" modal and clicks submit.
2. Frontend sends `POST /api/students` with JSON payload.
3. In `backend/app.py`, `add_student()` extracts `data = request.get_json()`.
4. Loops over `required_fields`: `student_id`, `student_name`, `phone`, `program_id`.
5. Cursor executes parameterized `INSERT INTO STUDENT (...) VALUES (:student_id, ...)`.
6. `conn.commit()` commits transaction to Oracle.
7. Flask returns `HTTP 201 Created` with `{"message": "Student added successfully"}`.
8. Frontend refreshes table and closes modal.

### Workflow 3: Listing Scholarships (`GET /api/scholarships`)
1. User clicks **Scholarships** tab.
2. Frontend requests `GET /api/scholarships`.
3. In `backend/app.py`, `get_scholarships()` runs.
4. Executes SQL join between `SCHOLARSHIP`, `SCHOLARSHIP_APPLICATION`, and `STUDENT`.
5. Returns JSON array with student name, scholarship type, and amount.
6. Frontend populates `#scholarshipTableBody`.

### Workflow 4: Submitting a Scholarship Application (`POST /api/applications`)
1. Student submits application form.
2. Frontend sends `POST /api/applications` (`application_id`, `student_id`, `application_date`).
3. In `backend/app.py`, `add_application()` validates required keys.
4. Executes SQL: `INSERT INTO SCHOLARSHIP_APPLICATION (...) VALUES (:application_id, :student_id, TO_DATE(:date, 'YYYY-MM-DD'), 'Pending')`.
5. `conn.commit()` commits the new pending application.
6. Returns `HTTP 201 Created` with `"status": "Pending"`.

### Workflow 5: Updating Application Status (`PUT /api/applications/<id>/status`)
1. Admin reviews application and selects `Approved` or `Rejected`.
2. Frontend sends `PUT /api/applications/APP001/status` with `{"status": "Approved"}`.
3. In `backend/app.py`, `update_application_status()` verifies status $\in \{\text{'Pending'}, \text{'Approved'}, \text{'Rejected'}\}$.
4. Executes: `UPDATE SCHOLARSHIP_APPLICATION SET ApplicationStatus = :status WHERE ApplicationID = :id`.
5. Verifies `cursor.rowcount > 0` (raises 404 if application not found).
6. Commits and returns `HTTP 200 OK`.

### Workflow 6: Creating a Disbursement (`POST /api/disbursements`)
1. Admin initiates payout for scholarship `SCH001`.
2. Frontend sends `POST /api/disbursements` with account number, amount, date, and mode.
3. In `backend/app.py`, `add_disbursement()` validates mode $\in \{\text{'Bank Transfer'}, \text{'Direct Transfer'}\}$.
4. Queries `SCHOLARSHIP` to ensure scholarship exists; queries `BANK_ACCOUNT` to ensure account exists.
5. Executes `INSERT INTO DISBURSEMENT (...) VALUES (...)`.
6. Commits transaction and returns `HTTP 201 Created`.

### Workflow 7: Recording Fee Payments with Overpayment Prevention (`POST /api/payments`)
1. Student pays tuition installment of ₹10,000 via UPI.
2. Frontend sends `POST /api/payments` with `fee_id`, `method_id`, `amount_paid`, `transaction_id`.
3. In `backend/app.py`, `add_payment()` parses payload.
4. Executes `INSERT INTO FEE_PAYMENT (PaymentID, FeeID, MethodID, PaymentDate, AmountPaid, TransactionID) VALUES (...)`.
5. **Database Trigger Execution:**
   - Oracle PL/SQL trigger `TRG_CHECK_FEE_PAYMENT` intercepts insertion.
   - Calculates `v_total_paid + :NEW.AmountPaid`.
   - If sum exceeds `v_fee_amount`, trigger calls `RAISE_APPLICATION_ERROR(-20001, 'Payment exceeds the total fee amount.')`.
   - Python catches `oracledb.DatabaseError`, issues `conn.rollback()`, and returns `HTTP 400 Bad Request`.
   - If sum $\le \text{FeeAmount}$, insert succeeds, `conn.commit()` executes, and returns `HTTP 201 Created`.

### Workflow 8: Generating Dashboard Statistics (`GET /api/dashboard`)
1. Dashboard view opens.
2. Frontend requests `GET /api/dashboard`.
3. In `backend/app.py`, `get_dashboard()` executes analytical queries:
   - `SELECT COUNT(*) FROM STUDENT`
   - `SELECT COUNT(*), NVL(SUM(Amount), 0) FROM SCHOLARSHIP`
   - `SELECT NVL(SUM(FeeAmount), 0) FROM STUDENT_FEE`
   - `SELECT NVL(SUM(AmountPaid), 0) FROM FEE_PAYMENT`
   - `SELECT COUNT(*) FROM SCHOLARSHIP_APPLICATION WHERE ApplicationStatus = 'Pending'`
   - `SELECT COUNT(*) FROM SCHOLARSHIP_APPLICATION WHERE ApplicationStatus = 'Approved'`
4. Computes `total_outstanding = total_fees - total_paid`.
5. Returns composite JSON response. Frontend updates KPI cards and re-renders Chart.js visualizations.

### Workflow 9: Fetching & Displaying the Neo4j Graph (`GET /api/neo4j/graph`)
1. User clicks **Neo4j Graph Explorer** tab in `index.html`.
2. Frontend calls `fetchAPI('/api/neo4j/graph?limit=500')`.
3. In `backend/neo4j_routes.py`, `api_get_graph_data()` calls `graph_service.get_graph_data(limit=500)`.
4. Executes Cypher matching all nodes and edges:
   ```cypher
   MATCH (n) RETURN elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props LIMIT $limit
   ```
   Followed by relationship matching:
   ```cypher
   MATCH (n)-[r]->(m) WHERE elementId(n) IN $ids AND elementId(m) IN $ids
   RETURN elementId(r) AS rel_id, type(r) AS rel_type, elementId(n) AS src_id, elementId(m) AS tgt_id
   ```
5. Serializes payload into Cytoscape format: `{"elements": {"nodes": [...], "edges": [...]}}`.
6. Browser Cytoscape.js canvas receives elements and animates COSE physics layout.

### Workflow 10: Searching & Filtering Graph Data (`GET /api/neo4j/graph?student_id=S001`)
1. User selects "Aarav Sharma (S001) Ego Network" preset or types `S001` in graph search.
2. Frontend sends `GET /api/neo4j/graph?student_id=S001`.
3. `graph_service.get_graph_data(student_id='S001')` runs multi-hop path query:
   ```cypher
   MATCH (s:Student {studentId: $sid})
   OPTIONAL MATCH path = (s)-[*1..3]-(m)
   WITH s, collect(distinct m) AS related
   UNWIND [s] + related AS n
   RETURN DISTINCT elementId(n) AS elem_id, labels(n) AS labels, properties(n) AS props
   ```
4. Isolates all nodes within 3 relationship hops of student S001.
5. Returns subgraph. Cytoscape centers and highlights S001's immediate ecosystem (Program, Guardian, Profile, Applications, Fees).
