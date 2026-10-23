# Complete Codebase Analysis & Viva Preparation
# Deliverable 10: End-to-End Traceability Matrix

**Project Title:** Scholarship and Fee Management System  
**Traceability Scope:** User Action $\rightarrow$ Frontend Event $\rightarrow$ HTTP Request $\rightarrow$ Flask Router $\rightarrow$ Service Function $\rightarrow$ Database Driver $\rightarrow$ Query/Trigger $\rightarrow$ Storage Mutation $\rightarrow$ Response $\rightarrow$ UI Update  
**Evidence Level:** `[VERIFIED]` directly from source code across all layers.

---

## 1. Master End-to-End Traceability Matrix

The table below traces 7 representative real-world workflows from the user's browser down to the physical database storage engine and back to the screen:

| Workflow # & Name | User Action in Browser | Frontend Function & Event | Outgoing HTTP Request | Flask Route Handler | Backend Service Function | Database Driver & Protocol | SQL / PLSQL / Cypher Executed | Tables / Nodes / Edges Mutated | Backend HTTP Response | Client UI Update |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **WF-1: Student Registration** | Clicks "+ Add Student", fills modal form, and clicks "Save Student" | `addStudent(event)` on form `submit` (`index.html`) | `POST /api/students`<br>Content-Type: application/json | `add_student()` (`backend/app.py` L71) | Direct route handler execution | `oracledb.connect()` via `backend/db.py` (TCP Port 1521) | `INSERT INTO STUDENT (StudentID, StudentName, Phone, ProgramID, ...) VALUES (:student_id, ...)` | `STUDENT` table (1 new row inserted; FK checked against `PROGRAM`) | `HTTP 201 Created`<br>`{"message": "Student added successfully", "student_id": "S006"}` | Closes modal form; appends new row to `#studentTableBody`; updates `#totalStudents` metric card. |
| **WF-2: Scholarship Submission** | Submits scholarship application form for student `S001` | `submitApplication(event)` on form `submit` | `POST /api/applications`<br>JSON body | `add_application()` (`backend/app.py` L311) | Direct route handler execution | `oracledb.connect()` via `backend/db.py` | `INSERT INTO SCHOLARSHIP_APPLICATION (ApplicationID, StudentID, ApplicationDate, ApplicationStatus) VALUES (:app_id, :sid, TO_DATE(...), 'Pending')` | `SCHOLARSHIP_APPLICATION` table (1 row inserted with status `'Pending'`) | `HTTP 201 Created`<br>`{"message": "Scholarship application submitted", "status": "Pending"}` | Renders application in administrative table with amber `'Pending'` status badge. |
| **WF-3: Application Review & Status Update** | Admin selects "Approved" from dropdown and clicks "Update" | `updateAppStatus(id, 'Approved')` on `click` | `PUT /api/applications/APP001/status`<br>`{"status": "Approved"}` | `update_application_status(id)` (`backend/app.py` L531) | Direct route handler execution | `oracledb.connect()` via `backend/db.py` | `UPDATE SCHOLARSHIP_APPLICATION SET ApplicationStatus = :status WHERE ApplicationID = :id` | `SCHOLARSHIP_APPLICATION` table (`ApplicationStatus` updated to `'Approved'`) | `HTTP 200 OK`<br>`{"message": "Application status updated successfully", "status": "Approved"}` | Updates status badge to green `'Approved'`; enables "Award Scholarship" action button. |
| **WF-4: Scholarship Award (Neo4j)** | Admin enters grant amount of ₹50,000 and awards scholarship | `awardScholarship(event)` on form `submit` | `POST /api/neo4j/scholarships`<br>JSON body | `api_create_scholarship()` (`neo4j_routes.py` L411) | `graph_service.create_scholarship()` (`graph_service.py` L864) | `neo4j.GraphDatabase.driver()` (Bolt Port 7687) | Checks `a.applicationStatus == 'Approved'`; executes `CREATE (sch:Scholarship $props) WITH sch MATCH (a:Application) MERGE (a)-[:AWARDS]->(sch)` | 1 `:Scholarship` node created; 1 `[:AWARDS]` directed edge created | `HTTP 201 Created`<br>`{"message": "Scholarship awarded", "scholarship": {...}}` | Displays green alert banner; Cytoscape graph canvas dynamically spawns gold star `:Scholarship` node linked to `:Application`. |
| **WF-5: Fee Payment & Overpayment Prevention (Oracle)** | Student pays tuition installment of ₹10,000 | `addPaymentRecord(event)` on form `submit` | `POST /api/payments`<br>JSON body | `add_payment()` (`backend/app.py` L1061) | Direct route handler execution | `oracledb.connect()` via `backend/db.py` | `INSERT INTO FEE_PAYMENT (PaymentID, FeeID, MethodID, AmountPaid, ...) VALUES (...)`.<br>Fires trigger `TRG_CHECK_FEE_PAYMENT`. | `FEE_PAYMENT` table (1 row inserted; rejected if `v_total_paid + AmountPaid > FeeAmount`) | `HTTP 201 Created`<br>`{"message": "Fee payment recorded successfully"}` (or `HTTP 400` if overpayment) | Re-calculates `remainingFee`; updates status badge to `'Paid'` if zero; updates Chart.js financial progress bar. |
| **WF-6: System KPI Dashboard** | User enters or refreshes the overview dashboard | `loadDashboard()` on page `load` | `GET /api/dashboard` | `get_dashboard()` (`backend/app.py` L1198) | Direct route handler execution | `oracledb.connect()` via `backend/db.py` | Aggregates `COUNT(*)` from `STUDENT`, `SCHOLARSHIP`, `SUM(FeeAmount)` from `STUDENT_FEE`, `SUM(AmountPaid)` from `FEE_PAYMENT` | Reads across 4 relational tables; computes `total_outstanding = total_fees - total_paid` | `HTTP 200 OK`<br>`{"total_students": 5, "total_fees": 380000, "total_paid": 100000, ...}` | Populates 4 top summary metric cards; redraws Chart.js fee reconciliation and scholarship breakdown graphs. |
| **WF-7: Ego-Network Graph Visualization (Cytoscape)** | User clicks preset "Aarav Sharma (S001) Ego Network" | `loadGraphPreset('S001')` on preset `click` | `GET /api/neo4j/graph?student_id=S001` | `api_get_graph_data()` (`neo4j_routes.py` L512) | `graph_service.get_graph_data()` (`graph_service.py` L2055) | `neo4j.GraphDatabase.driver()` (Bolt Port 7687) | Cypher: `MATCH (s:Student {studentId: $sid}) OPTIONAL MATCH path = (s)-[*1..3]-(m) UNWIND ... RETURN DISTINCT nodes & edges` | Traverses in-memory graph pointers up to 3 hops without table scans | `HTTP 200 OK`<br>`{"elements": {"nodes": [...], "edges": [...]}}` formatted for Cytoscape.js | Clears canvas; loads S001 subgraph; runs COSE physics simulation; centers camera on S001 royal blue circle node. |

---

## 2. In-Depth Trace: Financial Payment Workflow (WF-5)

To prepare you for viva questions asking you to trace a complete transaction, here is the granular, step-by-step trace of Workflow 5:

```
[1. User Action]
Student clicks "Make Payment" in index.html for Fee ID 'F001' with Amount '₹10,000'.

[2. Browser DOM Interception (index.html)]
Event Listener: document.getElementById("feeForm").addEventListener("submit", addPaymentRecord)
JavaScript reads:
  feeId = "F001"
  amountPaid = 10000
  methodId = "M01" (UPI)
  paymentDate = "2026-10-22"
  transactionId = "TXN" + Date.now()

Client Validation:
  if (amountPaid <= 0) -> showMessage("Amount must be positive", true); return;

[3. Network Transmission]
fetch("http://127.0.0.1:5000/api/payments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    payment_id: "PAY006",
    fee_id: "F001",
    method_id: "M01",
    payment_date: "2026-10-22",
    amount_paid: 10000,
    transaction_id: "TXN10006"
  })
})

[4. Flask Routing (backend/app.py)]
Flask matches route: @app.route("/api/payments", methods=["POST"])
Function invoked: add_payment()
request.get_json() parses JSON into Python dictionary 'data'.

Required field check:
for field in ["payment_id", "fee_id", "method_id", "payment_date", "amount_paid", "transaction_id"]:
    if field not in data: return jsonify({"error": f"Missing {field}"}), 400

[5. Database Connection (backend/db.py)]
conn = get_connection()
cursor = conn.cursor()

[6. SQL Statement Execution]
cursor.execute("""
    INSERT INTO FEE_PAYMENT (
        PaymentID, FeeID, ScholarshipID, MethodID, PaymentDate, AmountPaid, TransactionID
    )
    VALUES (
        :payment_id, :fee_id, :scholarship_id, :method_id,
        TO_DATE(:payment_date, 'YYYY-MM-DD'), :amount_paid, :transaction_id
    )
""", { ... bind parameters ... })

[7. Oracle PL/SQL Trigger Execution (Inside Oracle Engine)]
Oracle listener catches BEFORE INSERT event on FEE_PAYMENT for each row.
Trigger TRG_CHECK_FEE_PAYMENT executes:
  1. SELECT FeeAmount INTO v_fee_amount FROM STUDENT_FEE WHERE FeeID = 'F001';
     -> v_fee_amount = 75000
  2. SELECT NVL(SUM(AmountPaid), 0) INTO v_total_paid FROM FEE_PAYMENT WHERE FeeID = 'F001';
     -> v_total_paid = 35000
  3. Condition Check:
     IF (35000 + 10000) > 75000 -> 45000 > 75000 is FALSE.
  4. Insertion permitted to proceed physically to data blocks.

[8. Transaction Commit]
conn.commit() executes. Oracle writes redo log entry, releases locks, and returns success code to Python.

[9. HTTP Response]
Flask returns HTTP 201 Created:
jsonify({
    "message": "Fee payment recorded successfully",
    "payment_id": "PAY006",
    "transaction_id": "TXN10006"
})

[10. Browser DOM Update]
Client receives HTTP 201:
  - Displays green toast banner: "Fee payment recorded successfully."
  - Calls renderFeeRecords(): queries /api/fees, updates remaining fee from ₹40,000 to ₹30,000.
  - Updates summary dashboard cards and redraws Chart.js fee progress chart.
```
