# Member 2 Backend Handoff Document for Member 3

- **Author:** Member 2 — Backend and Neo4j Implementation Engineer
- **Audience:** Member 3 (Query, Evaluation, and Financial Implementation / Testing Engineer) & Team
- **Project:** Scholarship and Fee Management System
- **Working Branch:** `feature/da3-neo4j-backend`
- **Date:** 20 October 2026

---

## 1. Executive Summary & Purpose

This document provides Member 3 with the verified integration specifications, ownership boundaries, reusable service primitives, academic API contracts, and financial integration points delivered by Member 2 for Phase 2 of DA-3.

All academic endpoints are fully registered, validated, and verified through a 94-test automated test suite (91 mock unit tests + 3 live Neo4j integration tests).

---

## 2. Ownership Boundaries

To avoid duplicate work, conflicting endpoints, or merge friction, the responsibilities are cleanly divided as agreed:

### Member 2 Responsibilities (Completed & Active)
- **Neo4j Connection Management:** Driver reuse (`@lru_cache`), safe environment loading, lifecycle management, connection health.
- **Academic Graph Service Foundation:** Cypher queries, parameterization, canonical identifiers, input whitelisting.
- **Core Academic APIs:**
  - Students (`/api/neo4j/students`, `/api/neo4j/students/<id>`, `/api/neo4j/students/<id>/profile`, `/api/neo4j/students/<id>/guardians`)
  - Departments & Programs (`/api/neo4j/departments`, `/api/neo4j/departments/<id>`, `/api/neo4j/programs`, `/api/neo4j/programs/<id>/students`)
  - Applications (`/api/neo4j/applications`, `/api/neo4j/applications/<id>`, `/api/neo4j/applications/<id>/status`, `/api/neo4j/students/<id>/applications`)
  - Scholarships (`/api/neo4j/scholarships`, `/api/neo4j/scholarships/<id>`, `POST /api/neo4j/scholarships`)
  - Generic Foundation (`/api/neo4j/nodes/<label>`, `/api/neo4j/nodes/<label>/<id>`)
- **Academic Business Rules:** Non-negative amounts, application status domain validation, prerequisite check on scholarship awards (Approved applications only), and 1:1 application-scholarship constraint.
- **Flask Integration Architecture:** Flask Blueprint `neo4j_bp` mounted at `/api/neo4j`, CORS enabled, dual-context execution compatibility.

### Member 3 Responsibilities (Preserved for Member 3 Ownership)
- **Financial Services & Endpoints:**
  - Fees (`Fee` node operations, student fee lookups).
  - Payments (`Payment` node creation and listing).
  - Payment Methods (`PaymentMethod` node listing).
  - Bank Accounts & Disbursements (`BankAccount`, `Disbursement` node lookups).
- **Financial Business Rules:**
  - Cumulative fee payments not exceeding `Fee.feeAmount`.
  - Transaction ID uniqueness enforcement.
  - Disbursement mode validation (`Bank Transfer`, `Direct Transfer`).
- **Graph Queries & Evaluation:**
  - Analytical queries in `05_graph_queries.cypher` and `06_query_verification.cypher`.
  - Comparative evaluation between Oracle and Neo4j (`docs/da3_oracle_vs_neo4j.md`).
  - Test matrix execution for query benchmarks (N3-01 through N3-16).

---

## 3. Available Connection & Service Primitives

Member 3 can import and reuse the following tested primitives directly from `backend.neo4j_db` and `backend.graph_service`:

### Database Driver & Session (`backend/neo4j_db.py`)
```python
from backend.neo4j_db import get_driver, get_database_name, verify_connection

# Reusing driver singleton:
driver = get_driver()
db_name = get_database_name()

# Executing safe read or write transactions:
with driver.session(database=db_name) as session:
    result = session.run("MATCH (f:Fee {feeId: $id}) RETURN properties(f) AS fee", id="F001").single()
```

### Shared Serialization & Exceptions (`backend/graph_service.py`)
```python
from backend.graph_service import (
    clean_graph_item,       # Recursively converts neo4j.time.Date to ISO string, Maps to dicts
    GraphServiceError,      # Base exception (HTTP 500)
    InvalidInputError,      # Validation exception (HTTP 400)
    NotFoundError,          # Missing entity exception (HTTP 404)
    ConflictError,          # Duplicate / rule violation (HTTP 409)
    NODE_IDENTIFIERS,       # Dictionary mapping labels to primary keys
    ALLOWED_PROPERTIES,     # Dictionary mapping labels to approved properties
)
```

---

## 4. Academic API Contract for Member 3

All endpoints are hosted at `http://127.0.0.1:5000/api/neo4j/*` and accept/return `Content-Type: application/json`.

### 4.1 Students
- `GET /api/neo4j/students?limit=100`:
  Returns `{"count": N, "students": [{"studentId": "...", "studentName": "...", "programName": "...", ...}]}` (200).
- `GET /api/neo4j/students/<student_id>`:
  Returns `{"student": {"studentId": "...", "program": {...}, "department": {...}}}` (200) or `{"error": "..."}` (404).
- `POST /api/neo4j/students`:
  Request body:
  ```json
  {
    "studentId": "S100",
    "studentName": "Rahul Sharma",
    "phone": "9876543210",
    "programId": "P01",
    "city": "Chennai"
  }
  ```
  Returns `{"student": {...}}` (201). Fails with 400 if `programId` does not exist; fails with 409 if `studentId` already exists.
- `GET /api/neo4j/students/<student_id>/profile`:
  Returns `{"studentId": "...", "profile": {...}}` (200) or 404 if student/profile missing.
- `GET /api/neo4j/students/<student_id>/guardians`:
  Returns `{"studentId": "...", "guardians": [...], "count": N}` (200).

### 4.2 Departments & Programs
- `GET /api/neo4j/departments`: Returns `{"departments": [...], "count": N}` (200).
- `GET /api/neo4j/departments/<dept_id>`: Returns `{"department": {...}, "programs": [...]}` (200) or 404.
- `GET /api/neo4j/programs`: Returns `{"programs": [...], "count": N}` (200).
- `GET /api/neo4j/programs/<program_id>/students`: Returns `{"programId": "...", "programName": "...", "students": [...], "count": N}` (200).

### 4.3 Applications
- `GET /api/neo4j/applications?status=Approved`: Returns `{"applications": [...], "count": N}` (200).
- `GET /api/neo4j/applications/<application_id>`: Returns `{"application": {...}, "student": {...}, "scholarship": {...}}` (200).
- `POST /api/neo4j/applications`:
  Request body:
  ```json
  {
    "applicationId": "APP101",
    "studentId": "S001",
    "applicationStatus": "Pending"
  }
  ```
  Returns `{"application": {...}}` (201). Automatically links `(Student)-[:SUBMITTED]->(Application)`.
- `PUT /api/neo4j/applications/<application_id>/status`:
  Request body: `{"status": "Approved"}` (must be `'Pending'`, `'Approved'`, or `'Rejected'`). Returns updated application (200).
- `GET /api/neo4j/students/<student_id>/applications`: Returns `{"studentId": "...", "applications": [...], "count": N}` (200).

### 4.4 Scholarships
- `GET /api/neo4j/scholarships`: Returns `{"scholarships": [...], "count": N}` (200).
- `GET /api/neo4j/scholarships/<scholarship_id>`: Returns `{"scholarship": {...}, "application": {...}, "student": {...}, "disbursements": [...]}` (200).
- `POST /api/neo4j/scholarships`:
  Request body:
  ```json
  {
    "scholarshipId": "SCH101",
    "applicationId": "APP001",
    "scholarshipType": "Merit Scholarship",
    "amount": 50000.0
  }
  ```
  Returns `{"scholarship": {...}}` (201). Automatically links `(Application)-[:AWARDS]->(Scholarship)`.
  **Enforced Rules:**
  - `amount >= 0` (400 if negative or non-numeric).
  - Target application must exist (400 if missing).
  - Target application must have `applicationStatus == 'Approved'` (409 if `Pending` or `Rejected`).
  - Target application must not already have an awarded scholarship (409 if duplicate award).

---

## 5. Integration Points for Financial Endpoints (Member 3)

When Member 3 implements the financial routes:
1. **Mounting:** Add route decorators directly onto `neo4j_bp` in `backend/neo4j_routes.py` (e.g. `@neo4j_bp.route("/fees", ...)`), or create a dedicated `financial_routes.py` Blueprint.
2. **Linking Payments to Fees:**
   - In Cypher: `MATCH (f:Fee {feeId: $feeId}), (p:Payment {paymentId: $paymentId}) MERGE (f)-[:HAS_PAYMENT]->(p)`
3. **Cumulative Overpayment Protection:**
   - Use Cypher read-write transaction:
     ```cypher
     MATCH (f:Fee {feeId: $feeId})
     OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
     WITH f.feeAmount AS totalFee, coalesce(sum(p.amountPaid), 0) AS totalPaid
     RETURN totalFee, totalPaid, (totalFee - totalPaid) AS outstanding
     ```
     If `$newPaymentAmount > outstanding`, raise `ConflictError("Payment amount exceeds outstanding fee balance.")`.
4. **Optional Scholarship Links on Payments:**
   - Use `OPTIONAL MATCH` or conditional `MERGE`:
     ```cypher
     MATCH (p:Payment {paymentId: $paymentId})
     WITH p WHERE $scholarshipId IS NOT NULL
     MATCH (sch:Scholarship {scholarshipId: $scholarshipId})
     MERGE (p)-[:USES_SCHOLARSHIP]->(sch)
     ```

---

## 6. Open Coordination Items & Discrepancies

1. **Sample Data Conflict in Baseline (`APP002` & `APP004`):**
   - In Member 1's `02_import_data.cypher`, `SCH002` is linked to `APP002` (`Pending`) and `SCH004` is linked to `APP004` (`Rejected`).
   - Member 2's backend strictly enforces the rule for all *new* scholarship creations (`POST /api/neo4j/scholarships`). Historical records in the sample data remain readable.
   - Recommended team consensus: Report this inherited discrepancy in the final DA-3 evaluation report.
2. **Shared Database Migration Execution:**
   - The shared container `scholarship-neo4j` currently holds 0 nodes.
   - Member 1's scripts (`01_constraints.cypher`, `02_import_data.cypher`, `03_create_relationships.cypher`) are ready in `origin/feature/da3-graph-schema`. Once migration execution is authorized by the repository owner, the 54 sample nodes can be populated.
