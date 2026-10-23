# DA-3 Integration & End-to-End Test Plan

**Project:** Scholarship and Fee Management System  
**Lead Author:** Member 2 (Backend, Graph Service & Integration Engineer)  
**Collaborators:** Member 1 (Database & Schema), Member 3 (Financial & Frontend)  
**Date:** 21 October 2026  
**Status:** Approved Test Architecture for DA-3 Integration  

---

## 1. Objective and Testing Philosophy

This test plan defines the end-to-end verification pipeline required to validate the complete DA-3 Neo4j implementation across all three team members while safeguarding the existing DA-2 Oracle system.

Testing follows five staged verification gates:
1. **Stage 1:** Graph Schema & Migration Data Integrity (Member 1).
2. **Stage 2:** Academic Graph APIs & Business Rules (Member 2).
3. **Stage 3:** Financial Graph APIs & Dashboard Aggregations (Member 3).
4. **Stage 4:** Frontend UI Integration & Cross-Engine Compatibility (Member 3 & Member 2).
5. **Stage 5:** Full Regression & Non-Interference Verification.

---

## 2. Stage 1: Schema & Migration Data Verification (Member 1)

*Execution Pre-condition: Requires user authorization to run `cypher-shell` with Member 1's migration scripts.*

### Test Cases

| Test ID | Objective | Cypher Query / Test Method | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-S1-01** | Constraint Verification | `SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties` | Exactly 12 UNIQUE constraints registered for the 12 canonical labels. | PLANNED (Awaiting Migration) |
| **TC-S1-02** | Node Counts by Label | `MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label` | Total 54 nodes across 12 canonical labels matching Member 1 schema documentation. | PLANNED (Awaiting Migration) |
| **TC-S1-03** | Relationship Counts | `MATCH ()-[r]->() RETURN type(r) AS relType, count(r) AS count ORDER BY relType` | Relationships match agreed topology (12 distinct relationship types). | PLANNED (Awaiting Migration) |
| **TC-S1-04** | Missing Primary Keys | `MATCH (n) WHERE n.studentId IS NULL AND n.deptId IS NULL AND n.programId IS NULL AND ... RETURN count(n)` | Exactly 0 nodes without their canonical primary key. | PLANNED (Awaiting Migration) |
| **TC-S1-05** | Referential Integrity (Orphans) | `MATCH (s:Student) WHERE NOT (s)<-[:HAS_STUDENT]-(:Program) RETURN count(s)` | Exactly 0 orphaned students without a parent program. | PLANNED (Awaiting Migration) |
| **TC-S1-06** | Sample Data Consistency | `MATCH (a:Application)-[:AWARDS]->(s:Scholarship) WHERE a.applicationStatus <> 'Approved' RETURN count(a)` | Resolving the `SCH002` / `SCH004` status discrepancy. | PLANNED (Member 1 Action) |

---

## 3. Stage 2: Member 2 Academic API Verification

*Execution Pre-condition: Virtual environment active (`backend/venv`), test suite executed via `pytest`.*

### Test Cases

| Test ID | Objective | Endpoint & HTTP Method | Test Payload / Action | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-A2-01** | Health Check (Available) | `GET /api/neo4j/health` | None | `200 OK`, `{"database": "neo4j", "status": "ok"}` | VERIFIED (Automated) |
| **TC-A2-02** | Health Check (Down) | `GET /api/neo4j/health` | Simulated connection failure | `503 Service Unavailable`, `{"status": "unavailable"}` | VERIFIED (Automated) |
| **TC-A2-03** | List Students Paginated | `GET /api/neo4j/students?limit=10` | Limit parameter | `200 OK`, array with max 10 items, count field | VERIFIED (Automated) |
| **TC-A2-04** | Create Student Valid | `POST /api/neo4j/students` | Valid student with existing `programId` | `201 Created`, student object with program link | VERIFIED (Automated) |
| **TC-A2-05** | Create Student Duplicate | `POST /api/neo4j/students` | Existing `studentId` | `409 Conflict`, error message | VERIFIED (Automated) |
| **TC-A2-06** | Create Student Invalid Program | `POST /api/neo4j/students` | Non-existent `programId` | `400 Bad Request`, referenced program does not exist | VERIFIED (Automated) |
| **TC-A2-07** | Create Student Missing Fields | `POST /api/neo4j/students` | Missing `phone` or `studentName` | `400 Bad Request`, validation error | VERIFIED (Automated) |
| **TC-A2-08** | Get Student Detail | `GET /api/neo4j/students/<id>` | Existing student ID | `200 OK`, nested program & department details | VERIFIED (Automated) |
| **TC-A2-09** | Get Student Profile | `GET /api/neo4j/students/<id>/profile` | Existing student with profile | `200 OK`, profile object | VERIFIED (Automated) |
| **TC-A2-10** | Get Student Guardians | `GET /api/neo4j/students/<id>/guardians` | Existing student | `200 OK`, array of guardian objects | VERIFIED (Automated) |
| **TC-A2-11** | List Programs & Students | `GET /api/neo4j/programs/<id>/students` | Existing program ID | `200 OK`, list of enrolled students | VERIFIED (Automated) |
| **TC-A2-12** | Create Application Valid | `POST /api/neo4j/applications` | Valid student ID, default Pending | `201 Created`, atomic `[:SUBMITTED]` link created | VERIFIED (Automated) |
| **TC-A2-13** | Update Application Status | `PUT /api/neo4j/applications/<id>/status` | `{"status": "Approved"}` | `200 OK`, updated status reflected in graph | VERIFIED (Automated) |
| **TC-A2-14** | Award Scholarship Valid | `POST /api/neo4j/scholarships` | Approved application, positive amount | `201 Created`, atomic `[:AWARDS]` link created | VERIFIED (Automated) |
| **TC-A2-15** | Reject Scholarship for Pending | `POST /api/neo4j/scholarships` | Application with status `'Pending'` | `409 Conflict`, rejection enforced by business rule | VERIFIED (Automated) |
| **TC-A2-16** | Reject Scholarship for Rejected | `POST /api/neo4j/scholarships` | Application with status `'Rejected'` | `409 Conflict`, rejection enforced by business rule | VERIFIED (Automated) |
| **TC-A2-17** | Reject Duplicate Award (1:1) | `POST /api/neo4j/scholarships` | Application already having scholarship | `409 Conflict`, application already has award | VERIFIED (Automated) |
| **TC-A2-18** | Reject Negative Amount | `POST /api/neo4j/scholarships` | `amount: -5000` | `400 Bad Request`, amount must be non-negative | VERIFIED (Automated) |
| **TC-A2-19** | Generic CRUD Protection | `POST /api/neo4j/nodes/Unknown` | Non-allowlisted label | `400 Bad Request`, unsupported node label | VERIFIED (Automated) |
| **TC-A2-20** | Live Fixture Cleanup | `tests/test_neo4j_live.py` | Create, verify, delete temporary nodes | `200 OK`, zero residual nodes left in shared DB | VERIFIED (Automated) |

---

## 4. Stage 3: Member 3 Financial API Verification (Planned)

*Execution Pre-condition: Member 3 registers financial routes on `neo4j_bp`.*

### Test Cases

| Test ID | Objective | Endpoint & HTTP Method | Test Payload / Action | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-F3-01** | List Student Fees | `GET /api/neo4j/fees` | Query fees | `200 OK`, fee array with dueDate & feeAmount | PLANNED (Member 3) |
| **TC-F3-02** | Create Fee Invoice | `POST /api/neo4j/fees` | Valid student, amount, dueDate | `201 Created`, atomic `[:HAS_FEE]` created | PLANNED (Member 3) |
| **TC-F3-03** | Record Fee Payment | `POST /api/neo4j/payments` | Valid feeId, methodId, amountPaid | `201 Created`, `[:HAS_PAYMENT]` & `[:PAID_VIA]` | PLANNED (Member 3) |
| **TC-F3-04** | Payment with Scholarship | `POST /api/neo4j/payments` | Valid payment including scholarshipId | `201 Created`, atomic `[:USES_SCHOLARSHIP]` | PLANNED (Member 3) |
| **TC-F3-05** | Disburse Scholarship | `POST /api/neo4j/disbursements` | Valid scholarshipId, accountNo, amount | `201 Created`, `[:HAS_DISBURSEMENT]` & `[:TO_ACCOUNT]` | PLANNED (Member 3) |
| **TC-F3-06** | Financial Dashboard | `GET /api/neo4j/dashboard` | Dashboard aggregation | `200 OK`, totalFees, totalPaid, totalDisbursed | PLANNED (Member 3) |
| **TC-F3-07** | Overpayment Validation | `POST /api/neo4j/payments` | Payment exceeding remaining fee | `400 Bad Request` or business rule warning | PLANNED (Member 3) |

---

## 5. Stage 4: Frontend UI Integration & Cross-Engine Usability

*Execution Pre-condition: Local web server running serving `index.html`.*

### Test Cases

| Test ID | Objective | UI Interaction / Component | Verification Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-UI-01** | Oracle API Preservation | Standard page load & tab browsing | Oracle `/api/*` requests complete successfully with zero regressions. | VERIFIED (Protected) |
| **TC-UI-02** | Database Mode Selector | Database toggle switch / tab | UI allows selecting between Oracle and Neo4j backends. | PLANNED (Member 3) |
| **TC-UI-03** | Academic Student Rendering | Students tab (Neo4j mode) | Renders students, program names, and departments accurately from `/api/neo4j/students`. | PLANNED (Member 3) |
| **TC-UI-04** | Scholarship Workflow UI | Applications tab (Neo4j mode) | Status badge rendering (`Pending`, `Approved`, `Rejected`), button to award scholarship enabled only on approved items. | PLANNED (Member 3) |
| **TC-UI-05** | Error Feedback Handling | Create duplicate student via UI | UI displays user-friendly error banner without crashing. | PLANNED (Member 3) |
| **TC-UI-06** | Zero Secret Exposure | Inspect network traffic & page source | No passwords, tokens, or raw connection strings visible in console or network requests. | VERIFIED |

---

## 6. Stage 5: Final Regression & Non-Interference Verification

### Test Cases

| Test ID | Objective | Action | Verification Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-REG-01** | Full Automated Suite | `python -m pytest -v` | 100% pass rate (all 94+ tests pass, 0 failures). | VERIFIED |
| **TC-REG-02** | Oracle Route Integrity | `tests/test_app_integration.py` | All 19 pre-existing Oracle endpoints remain active and return 200/400 as expected. | VERIFIED |
| **TC-REG-03** | DA-2 Codebase Immutability | `git diff --stat backend/db.py database/ frontend/ index.html` | Exactly 0 modified lines across all DA-2 artifacts. | VERIFIED |
| **TC-REG-04** | Live Database Isolation | `docker exec scholarship-neo4j cypher-shell "MATCH (n) RETURN count(n);"` | Shared database is not polluted with automated test records. | VERIFIED |
