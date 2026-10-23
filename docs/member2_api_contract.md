# Member 2 API Contract & Integration Guide

**Author:** Member 2 (Backend, Graph Service & Integration Engineer)  
**Target:** Member 3 (Financial APIs, Query Evaluation & Frontend Integration)  
**Date:** 21 October 2026  
**Status:** Active Contract for Phase 2 Backend  
**Blueprint Prefix:** `/api/neo4j`  

---

## 1. Overview & Architectural Boundaries

Member 2 has implemented the core Neo4j driver lifecycle, generic graph service, input validation, and academic REST endpoints under the Flask Blueprint `neo4j_bp` (prefix: `/api/neo4j`).

This document provides:
1. The exhaustive specification of all **21 endpoints that actually exist** in Member 2's implementation.
2. The reusable backend infrastructure (driver, transaction wrappers, serialization, and error classes) that Member 3 can leverage directly.
3. The integration contract and blueprint extension pattern for Member 3's pending **Financial APIs**.
4. The frontend integration protocol to ensure DA-2 Oracle routes remain protected.

---

## 2. Active Neo4j Endpoints Inventory (21 Total)

### A. System & Health Endpoint

#### `GET /api/neo4j/health`
- **Purpose:** Verifies live connectivity to the Neo4j database without leaking credentials or internal addresses.
- **Parameters:** None.
- **Request Body:** None.
- **Response (200 OK):**
  ```json
  {
    "database": "neo4j",
    "status": "ok"
  }
  ```
- **Error Responses:**
  - `503 Service Unavailable`: `{"database": "neo4j", "status": "unavailable"}` when the driver cannot reach the database.
- **Dependencies:** `backend.neo4j_db.verify_connection()`, Cypher: `RETURN 1 AS result`.

---

### B. Student Endpoints

#### 1. `GET /api/neo4j/students`
- **Purpose:** List students with their enrolled program and department details.
- **Query Parameters:**
  - `limit` (Optional, integer between 1 and 500, default `100`).
- **Response (200 OK):**
  ```json
  {
    "students": [
      {
        "studentId": "S001",
        "studentName": "Aarav Sharma",
        "phone": "9876543210",
        "houseNo": "12A",
        "street": "MG Road",
        "city": "Bengaluru",
        "pin": "560001",
        "programId": "P01",
        "programName": "B.Tech Computer Science and Engineering",
        "degreeLevel": "BTech",
        "deptName": "Computer Science and Engineering"
      }
    ],
    "count": 1
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: `{"error": "Limit must be an integer."}` or `{"error": "Limit must be between 1 and 500."}`.
  - `503 Service Unavailable`: `{"error": "Neo4j query failed."}`.
- **Graph Dependencies:** `(s:Student)`, `OPTIONAL MATCH (p:Program)-[:HAS_STUDENT]->(s)`, `OPTIONAL MATCH (d:Department)-[:HAS_PROGRAM]->(p)`.

#### 2. `GET /api/neo4j/students/<student_id>`
- **Purpose:** Retrieve full details for an individual student including program and department objects.
- **Path Parameter:** `student_id` (String, Required).
- **Response (200 OK):**
  ```json
  {
    "student": {
      "studentId": "S001",
      "studentName": "Aarav Sharma",
      "phone": "9876543210",
      "city": "Bengaluru",
      "program": {
        "programId": "P01",
        "programName": "B.Tech Computer Science and Engineering",
        "degreeLevel": "BTech"
      },
      "department": {
        "deptId": "D01",
        "deptName": "Computer Science and Engineering"
      }
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Non-empty string identifier missing.
  - `404 Not Found`: `{"error": "Student 'S999' was not found."}`.

#### 3. `POST /api/neo4j/students`
- **Purpose:** Create a new student node and atomically link to their program.
- **Request Body (JSON):**
  ```json
  {
    "studentId": "S006",
    "studentName": "Kavya Patel",
    "phone": "9811223344",
    "programId": "P01",
    "city": "Ahmedabad",
    "pin": "380001"
  }
  ```
- **Validation Rules:**
  - `studentId`, `studentName`, `phone` are mandatory non-empty strings.
  - All properties must be in `ALLOWED_PROPERTIES["Student"]`.
  - If `programId` is provided, the referenced `Program` node **must exist** in the graph; otherwise an error is raised.
  - Duplicate `studentId` is rejected.
- **Response (201 Created):**
  ```json
  {
    "student": {
      "studentId": "S006",
      "studentName": "Kavya Patel",
      "phone": "9811223344",
      "programId": "P01",
      "city": "Ahmedabad",
      "pin": "380001"
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Missing required fields, referenced program does not exist, or unsupported property keys.
  - `409 Conflict`: `{"error": "Student with identifier 'S006' already exists."}`.

#### 4. `GET /api/neo4j/students/<student_id>/profile`
- **Purpose:** Retrieve the profile associated with a student.
- **Graph Traversal:** `(s:Student {studentId: $id})-[:HAS_PROFILE]->(sp:StudentProfile)`.
- **Response (200 OK):**
  ```json
  {
    "studentId": "S001",
    "profile": {
      "studentId": "S001",
      "bloodGroup": "O+",
      "nationality": "Indian",
      "dateOfBirth": "2004-05-14",
      "email": "aarav.sharma@example.com"
    }
  }
  ```
- **Error Responses:**
  - `404 Not Found`: Student not found or student does not have a profile.

#### 5. `GET /api/neo4j/students/<student_id>/guardians`
- **Purpose:** Retrieve guardians for a student.
- **Graph Traversal:** `(s:Student {studentId: $id})-[:HAS_GUARDIAN]->(g:Guardian)`.
- **Response (200 OK):**
  ```json
  {
    "studentId": "S001",
    "guardians": [
      {
        "guardianId": "G001",
        "studentId": "S001",
        "guardianName": "Rajesh Sharma",
        "relation": "Father",
        "phoneNo": "9876501234",
        "emailId": "rajesh.sharma@example.com"
      }
    ],
    "count": 1
  }
  ```

#### 6. `GET /api/neo4j/students/<student_id>/applications`
- **Purpose:** Retrieve all scholarship applications submitted by a student.
- **Graph Traversal:** `(s:Student {studentId: $id})-[:SUBMITTED]->(a:Application) OPTIONAL MATCH (a)-[:AWARDS]->(sch:Scholarship)`.
- **Response (200 OK):**
  ```json
  {
    "studentId": "S001",
    "applications": [
      {
        "applicationId": "APP001",
        "studentId": "S001",
        "applicationDate": "2026-01-10",
        "applicationStatus": "Approved",
        "scholarship": {
          "scholarshipId": "SCH001",
          "scholarshipType": "Merit Scholarship",
          "amount": 50000.0
        }
      }
    ],
    "count": 1
  }
  ```

---

### C. Department & Program Endpoints

#### 7. `GET /api/neo4j/departments`
- **Purpose:** List all departments with their active program counts.
- **Graph Traversal:** `MATCH (d:Department) OPTIONAL MATCH (d)-[:HAS_PROGRAM]->(p:Program) RETURN properties(d), count(p)`.
- **Response (200 OK):**
  ```json
  {
    "departments": [
      {
        "deptId": "D01",
        "deptName": "Computer Science and Engineering",
        "programCount": 2
      }
    ],
    "count": 1
  }
  ```

#### 8. `GET /api/neo4j/departments/<dept_id>`
- **Purpose:** Retrieve department and array of programs offered.
- **Response (200 OK):**
  ```json
  {
    "department": { "deptId": "D01", "deptName": "Computer Science and Engineering" },
    "programs": [
      { "programId": "P01", "programName": "B.Tech Computer Science and Engineering", "degreeLevel": "BTech" }
    ]
  }
  ```

#### 9. `GET /api/neo4j/programs`
- **Purpose:** List all programs with their parent department name.
- **Response (200 OK):**
  ```json
  {
    "programs": [
      {
        "programId": "P01",
        "programName": "B.Tech Computer Science and Engineering",
        "degreeLevel": "BTech",
        "deptName": "Computer Science and Engineering"
      }
    ],
    "count": 1
  }
  ```

#### 10. `GET /api/neo4j/programs/<program_id>/students`
- **Purpose:** Retrieve all students enrolled in a specific academic program.
- **Graph Traversal:** `(p:Program {programId: $id})-[:HAS_STUDENT]->(s:Student)`.
- **Response (200 OK):**
  ```json
  {
    "programId": "P01",
    "programName": "B.Tech Computer Science and Engineering",
    "students": [
      { "studentId": "S001", "studentName": "Aarav Sharma", "phone": "9876543210" }
    ],
    "count": 1
  }
  ```

---

### D. Application Endpoints

#### 11. `GET /api/neo4j/applications`
- **Purpose:** List applications with optional status filter and student names.
- **Query Parameters:**
  - `limit` (Optional, 1-500, default 100).
  - `status` (Optional, string: `'Pending'`, `'Approved'`, or `'Rejected'`).
- **Response (200 OK):**
  ```json
  {
    "applications": [
      {
        "applicationId": "APP001",
        "studentId": "S001",
        "studentName": "Aarav Sharma",
        "applicationStatus": "Approved",
        "applicationDate": "2026-01-10",
        "scholarship": {
          "scholarshipId": "SCH001",
          "scholarshipType": "Merit Scholarship",
          "amount": 50000.0
        }
      }
    ],
    "count": 1
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Invalid status filter (must be Pending, Approved, or Rejected).

#### 12. `GET /api/neo4j/applications/<application_id>`
- **Purpose:** Retrieve an application by ID along with its student and awarded scholarship.
- **Response (200 OK):**
  ```json
  {
    "application": {
      "applicationId": "APP001",
      "studentId": "S001",
      "applicationStatus": "Approved",
      "applicationDate": "2026-01-10"
    },
    "student": {
      "studentId": "S001",
      "studentName": "Aarav Sharma"
    },
    "scholarship": {
      "scholarshipId": "SCH001",
      "scholarshipType": "Merit Scholarship",
      "amount": 50000.0
    }
  }
  ```

#### 13. `POST /api/neo4j/applications`
- **Purpose:** Create an application for an existing student and atomically link `(Student)-[:SUBMITTED]->(Application)`.
- **Request Body (JSON):**
  ```json
  {
    "applicationId": "APP006",
    "studentId": "S001",
    "applicationStatus": "Pending"
  }
  ```
- **Validation Rules:**
  - `studentId` must exist in graph.
  - `applicationStatus` defaults to `'Pending'`.
- **Response (201 Created):**
  ```json
  {
    "application": {
      "applicationId": "APP006",
      "studentId": "S001",
      "applicationStatus": "Pending"
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Student does not exist or status invalid.
  - `409 Conflict`: Application with `applicationId` already exists.

#### 14. `PUT /api/neo4j/applications/<application_id>/status`
- **Purpose:** Transition the workflow status of an application.
- **Request Body (JSON):**
  ```json
  {
    "status": "Approved"
  }
  ```
  *(Accepts either `"status"` or `"applicationStatus"` key).*
- **Validation Rules:** Status must be one of `{'Pending', 'Approved', 'Rejected'}`.
- **Response (200 OK):**
  ```json
  {
    "application": {
      "applicationId": "APP006",
      "studentId": "S001",
      "applicationStatus": "Approved"
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Missing status key or invalid status value.
  - `404 Not Found`: Application does not exist.

---

### E. Scholarship Endpoints

#### 15. `GET /api/neo4j/scholarships`
- **Purpose:** List scholarships with student details and application status.
- **Query Parameters:** `limit` (Optional, 1-500, default 100).
- **Response (200 OK):**
  ```json
  {
    "scholarships": [
      {
        "scholarshipId": "SCH001",
        "applicationId": "APP001",
        "scholarshipType": "Merit Scholarship",
        "amount": 50000.0,
        "applicationStatus": "Approved",
        "studentId": "S001",
        "studentName": "Aarav Sharma"
      }
    ],
    "count": 1
  }
  ```

#### 16. `GET /api/neo4j/scholarships/<scholarship_id>`
- **Purpose:** Retrieve scholarship details, awarded application, student, and linked disbursements.
- **Response (200 OK):**
  ```json
  {
    "scholarship": {
      "scholarshipId": "SCH001",
      "applicationId": "APP001",
      "scholarshipType": "Merit Scholarship",
      "amount": 50000.0
    },
    "application": { "applicationId": "APP001", "applicationStatus": "Approved" },
    "student": { "studentId": "S001", "studentName": "Aarav Sharma" },
    "disbursements": [
      {
        "disbursementId": "DIS001",
        "amount": 50000.0,
        "disbursementDate": "2026-02-10",
        "disbursementMode": "Bank Transfer"
      }
    ]
  }
  ```

#### 17. `POST /api/neo4j/scholarships`
- **Purpose:** Award a scholarship for an approved application.
- **Request Body (JSON):**
  ```json
  {
    "scholarshipId": "SCH006",
    "applicationId": "APP003",
    "scholarshipType": "Academic Excellence",
    "amount": 45000.0
  }
  ```
- **Strict Business Rules Enforced:**
  1. `amount` must be a non-negative finite number (`amount >= 0`).
  2. Referenced `Application` **must exist**.
  3. Referenced `Application` **must have status 'Approved'** (raises `409 Conflict` if `'Pending'` or `'Rejected'`).
  4. Referenced `Application` **must not already have an awarded scholarship** (1:1 award rule, raises `409 Conflict`).
  5. Duplicate `scholarshipId` raises `409 Conflict`.
- **Response (201 Created):**
  ```json
  {
    "scholarship": {
      "scholarshipId": "SCH006",
      "applicationId": "APP003",
      "scholarshipType": "Academic Excellence",
      "amount": 45000.0
    }
  }
  ```

---

### F. Generic CRUD Endpoints (Foundational)

#### 18. `GET /api/neo4j/nodes/<label>`
- **Purpose:** List nodes of an approved label (bounded pagination).
- **Parameters:** `label` (String in `NODE_IDENTIFIERS`), `limit` query param (1-500).

#### 19. `GET /api/neo4j/nodes/<label>/<identifier>`
- **Purpose:** Retrieve a single node by its canonical primary key.

#### 20. `POST /api/neo4j/nodes/<label>`
- **Purpose:** Create a single node with duplicate identifier prevention.

---

## 3. Financial APIs — Integration Requirements (Member 3 Ownership)

The following financial endpoints are **planned and NOT yet implemented**. Member 3 is responsible for designing, implementing, and registering these routes:

| Proposed Endpoint | HTTP Method | Expected Domain Purpose | Status |
| :--- | :--- | :--- | :--- |
| `/api/neo4j/fees` | `GET` | List student fees with payment totals and balance | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/fees` | `POST` | Generate fee invoices for students | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/fees/<fee_id>` | `GET` | Retrieve fee details with payments | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/payments` | `GET` | List fee payment transactions | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/payments` | `POST` | Record payments with method and optional scholarship | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/disbursements` | `GET` | List disbursements made to student bank accounts | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/disbursements` | `POST` | Disburse awarded scholarship funds | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/bank-accounts` | `GET`, `POST` | Manage student bank accounts for disbursements | **NOT IMPLEMENTED (Member 3)** |
| `/api/neo4j/dashboard` | `GET` | Graph-based KPI totals (fees collected, pending, awarded) | **NOT IMPLEMENTED (Member 3)** |

---

## 4. Reusable Backend Infrastructure for Member 3

Member 3 should **not** recreate driver connections, date formatters, or error classes. The following components in `backend/` are verified, tested, and ready for reuse:

### 1. Neo4j Connection Driver (`backend/neo4j_db.py`)
```python
from backend.neo4j_db import get_driver, get_database_name, verify_connection

# Usage:
driver = get_driver()
with driver.session(database=get_database_name()) as session:
    results = session.run("MATCH (f:Fee) RETURN f LIMIT 10")
```

### 2. Temporal Serialization (`backend/graph_service.py`)
Neo4j returns temporal objects (`neo4j.time.Date`, `neo4j.time.DateTime`) that cause Flask `jsonify` to crash with `TypeError: Object of type Date is not JSON serializable`.
```python
from backend.graph_service import clean_graph_item

# Recursively sanitizes dicts, lists, and records:
cleaned_data = clean_graph_item(raw_db_record)
```

### 3. Managed Transaction Utilities & Error Classes (`backend/graph_service.py`)
```python
from backend.graph_service import (
    GraphServiceError,
    InvalidInputError,  # Maps to HTTP 400
    NotFoundError,      # Maps to HTTP 404
    ConflictError,      # Maps to HTTP 409
    ALLOWED_PROPERTIES,
    NODE_IDENTIFIERS
)
```

### 4. Route Registration Pattern (`backend/neo4j_routes.py`)
All financial routes are registered on the `neo4j_bp` Blueprint with prefix `/api/neo4j`.

---

## 5. Active Financial & Dashboard Endpoints Inventory (16 Total)

### A. Dashboard Summary

#### `GET /api/neo4j/dashboard`
- **Purpose:** Aggregate live graph KPI totals across students, scholarships, fees, payments, and applications.
- **Response (200 OK):**
  ```json
  {
    "total_students": 5,
    "total_scholarships": 5,
    "total_scholarship_amount": 180000.0,
    "total_fees": 380000.0,
    "total_paid": 100000.0,
    "total_outstanding": 280000.0,
    "pending_applications": 1,
    "approved_applications": 3
  }
  ```

---

### B. Student Fee Endpoints

#### 1. `GET /api/neo4j/fees`
- **Purpose:** List student fees with amount paid and outstanding balances.
- **Parameters:** `limit` (optional integer, default 100).
- **Response (200 OK):**
  ```json
  {
    "count": 5,
    "fees": [
      {
        "feeId": "F001",
        "studentId": "S001",
        "studentName": "Aarav Sharma",
        "feeAmount": 75000.0,
        "dueDate": "2026-03-01",
        "amountPaid": 35000.0,
        "outstandingAmount": 40000.0,
        "FEEID": "F001",
        "STUDENTID": "S001"
      }
    ]
  }
  ```

#### 2. `GET /api/neo4j/fees/<fee_id>`
- **Purpose:** Retrieve fee details by identifier, including payment history list.
- **Response (200 OK):**
  ```json
  {
    "fee": {
      "feeId": "F001",
      "studentId": "S001",
      "studentName": "Aarav Sharma",
      "feeAmount": 75000.0,
      "amountPaid": 35000.0,
      "outstandingAmount": 40000.0,
      "payments": [
        {
          "paymentId": "PAY001",
          "amountPaid": 25000.0,
          "methodName": "UPI"
        }
      ]
    }
  }
  ```

#### 3. `POST /api/neo4j/fees`
- **Purpose:** Create a new fee linked to an existing student (`(Student)-[:HAS_FEE]->(Fee)`).
- **Request Body (supports camelCase or snake_case):**
  ```json
  {
    "fee_id": "F006",
    "student_id": "S001",
    "fee_amount": 50000.0,
    "due_date": "2026-04-01"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "message": "Student fee created successfully",
    "fee_id": "F006",
    "student_id": "S001",
    "fee_amount": 50000.0,
    "due_date": "2026-04-01"
  }
  ```

#### 4. `GET /api/neo4j/students/<student_id>/fees`
- **Purpose:** Retrieve all fees for a given student.
- **Response (200 OK):** Array envelope `{"fees": [...], "count": N}`.

---

### C. Fee Payment Endpoints

#### 1. `GET /api/neo4j/payments`
- **Purpose:** List payments with linked student, fee, payment method, and optional scholarship.
- **Response (200 OK):**
  ```json
  {
    "count": 5,
    "payments": [
      {
        "paymentId": "PAY001",
        "feeId": "F001",
        "studentId": "S001",
        "studentName": "Aarav Sharma",
        "methodName": "UPI",
        "paymentDate": "2026-02-25",
        "amountPaid": 25000.0,
        "transactionId": "TXN1001"
      }
    ]
  }
  ```

#### 2. `GET /api/neo4j/payments/<payment_id>`
- **Purpose:** Retrieve payment record by identifier.
- **Response (200 OK):** `{"payment": {...}}`.

#### 3. `POST /api/neo4j/payments`
- **Purpose:** Record a fee payment and atomically construct graph relationships:
  - `(Fee)-[:HAS_PAYMENT]->(Payment)`
  - `(Payment)-[:PAID_VIA]->(PaymentMethod)`
  - `(Payment)-[:USES_SCHOLARSHIP]->(Scholarship)` (if scholarshipId provided).
- **Business Rule Enforcement:** Enforces Oracle PL/SQL `TRG_CHECK_FEE_PAYMENT` rule: rejects payment if `totalPaid + amountPaid > feeAmount` with HTTP 400.
- **Request Body:**
  ```json
  {
    "payment_id": "PAY006",
    "fee_id": "F001",
    "method_id": "M01",
    "payment_date": "2026-03-01",
    "amount_paid": 5000.0,
    "transaction_id": "TXN1006",
    "scholarship_id": "SCH001"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "message": "Fee payment recorded successfully",
    "payment_id": "PAY006",
    "transaction_id": "TXN1006"
  }
  ```

#### 4. `GET /api/neo4j/students/<student_id>/payments`
- **Purpose:** Retrieve payments made for any fee of the given student.

---

### D. Scholarship Disbursement Endpoints

#### 1. `GET /api/neo4j/disbursements`
- **Purpose:** List disbursements with linked scholarship, student, and bank account.
- **Response (200 OK):** `{"disbursements": [...], "count": N}`.

#### 2. `GET /api/neo4j/disbursements/<disbursement_id>`
- **Purpose:** Retrieve single disbursement record.

#### 3. `POST /api/neo4j/disbursements`
- **Purpose:** Create disbursement linked to Scholarship and BankAccount:
  - `(Scholarship)-[:HAS_DISBURSEMENT]->(Disbursement)`
  - `(Disbursement)-[:TO_ACCOUNT]->(BankAccount)`
- **Business Rule Enforcement:** Validates `disbursement_mode` is `Bank Transfer` or `Direct Transfer`. Validates that total disbursed cannot exceed scholarship amount.
- **Request Body:**
  ```json
  {
    "disbursement_id": "DIS005",
    "scholarship_id": "SCH001",
    "account_no": "AC001",
    "disbursement_date": "2026-03-15",
    "amount": 10000.0,
    "disbursement_mode": "Bank Transfer"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "message": "Disbursement recorded successfully.",
    "disbursement_id": "DIS005"
  }
  ```

---

### E. Bank Account Endpoints

#### 1. `GET /api/neo4j/bank-accounts`
- **Purpose:** List bank accounts.

#### 2. `GET /api/neo4j/bank-accounts/<account_no>`
- **Purpose:** Retrieve bank account details by account number.

#### 3. `POST /api/neo4j/bank-accounts`
- **Purpose:** Create a new BankAccount node in the graph.
- **Request Body:**
  ```json
  {
    "account_no": "AC006",
    "bank_name": "State Bank of India",
    "ifsc": "SBIN0005678",
    "account_type": "Savings"
  }
  ```
- **Response (201 Created):** `{"message": "Bank account created successfully", "account_no": "AC006"}`.

---

### F. Student Scholarships Endpoint

#### `GET /api/neo4j/students/<student_id>/scholarships`
- **Purpose:** List all scholarships awarded to a student via `(Student)-[:SUBMITTED]->(Application)-[:AWARDS]->(Scholarship)`.
- **Response (200 OK):** `{"scholarships": [...], "count": N}`.

---

## 6. Frontend Dual-Engine Integration Protocol

1. **Dual-Engine Toggle:**
   - `index.html` includes an interactive header switch:
     - **Neo4j Property Graph (DA-3):** Routes requests to `/api/neo4j/*`.
     - **Oracle Relational SQL (DA-2):** Routes requests to original `/api/*`.
2. **Seamless Serialization:**
   - All Neo4j graph service endpoints return objects containing both camelCase (`studentId`, `feeAmount`) and UPPERCASE aliases (`STUDENTID`, `FEEAMOUNT`), allowing `index.html` table renders to display data identically regardless of active engine.
3. **DA-2 Invariant:**
   - All 19 original Oracle endpoints remain registered and functional on the Flask application.

