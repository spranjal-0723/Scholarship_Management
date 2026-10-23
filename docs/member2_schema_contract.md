# Member 2 Graph Schema Contract & Assumptions

**Author:** Member 2 (Backend & Integration Engineer)  
**Target:** Member 1 (Database & Graph Schema Engineer)  
**Date:** 21 October 2026  
**Status:** Working Contract for DA-3 Integration  
**Working Branch:** `feature/da3-neo4j-backend`  

---

## 1. Purpose & Scope

This document specifies the exact graph schema assumptions, node labels, canonical identifier keys, properties, relationship types, and constraints required by Member 2's backend implementation (`backend/graph_service.py` and `backend/neo4j_routes.py`). 

It provides Member 1 with an authoritative contract to verify against the migration scripts (`database/neo4j/01_constraints.cypher`, `02_import_data.cypher`, `03_create_relationships.cypher`, and `04_verify_graph.cypher`) before final schema merge into `main`.

---

## 2. Canonical Node Labels and Primary Identifiers

The backend enforces strict label validation via an allowlist of 12 canonical entity labels. Any operation referencing an unlisted label is rejected with `InvalidInputError`.

| Node Label | Canonical Identifier Property | Uniqueness Assumption | Constraint Name in `01_constraints.cypher` | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| `Department` | `deptId` | Unique | `department_deptId_unique` | VERIFIED |
| `Program` | `programId` | Unique | `program_programId_unique` | VERIFIED |
| `Student` | `studentId` | Unique | `student_studentId_unique` | VERIFIED |
| `StudentProfile` | `studentId` | Unique (1:1 with Student) | `studentProfile_studentId_unique` | VERIFIED |
| `Guardian` | `guardianId` | Unique | `guardian_guardianId_unique` | VERIFIED |
| `Application` | `applicationId` | Unique | `application_applicationId_unique` | VERIFIED |
| `Scholarship` | `scholarshipId` | Unique | `scholarship_scholarshipId_unique` | VERIFIED |
| `BankAccount` | `accountNo` | Unique | `bankAccount_accountNo_unique` | VERIFIED |
| `Disbursement` | `disbursementId` | Unique | `disbursement_disbursementId_unique` | VERIFIED |
| `Fee` | `feeId` | Unique | `fee_feeId_unique` | VERIFIED |
| `PaymentMethod` | `methodId` | Unique | `paymentMethod_methodId_unique` | VERIFIED |
| `Payment` | `paymentId` | Unique | `payment_paymentId_unique` | VERIFIED |

---

## 3. Node Properties and Types

Properties are validated against `ALLOWED_PROPERTIES` in `backend/graph_service.py`. The table below outlines properties required or consumed by Member 2's academic backend, expected data types, and status.

### A. Academic Entities (Member 2 Primary Domain)

#### 1. `Department`
- **Identifier:** `deptId` (String, Required)
- **Properties:**
  - `deptId`: String (e.g., `'D01'`) — Required
  - `deptName`: String (e.g., `'Computer Science'`) — Required
- **Verification Status:** `VERIFIED`

#### 2. `Program`
- **Identifier:** `programId` (String, Required)
- **Properties:**
  - `programId`: String (e.g., `'P01'`) — Required
  - `programName`: String (e.g., `'B.Tech CSE'`) — Required
  - `degreeLevel`: String (e.g., `'BTech'`, `'MTech'`, `'PhD'`) — Optional/Recommended
  - `deptId`: String (Foreign Key reference to `Department`) — Optional
- **Verification Status:** `VERIFIED`

#### 3. `Student`
- **Identifier:** `studentId` (String, Required)
- **Properties:**
  - `studentId`: String (e.g., `'S001'`) — Required
  - `studentName`: String — Required
  - `phone`: String — Required
  - `houseNo`: String — Optional
  - `street`: String — Optional
  - `city`: String — Optional
  - `pin`: String / Integer — Optional
  - `programId`: String (Foreign Key reference to `Program`) — Optional (used to create `[:HAS_STUDENT]`)
- **Verification Status:** `VERIFIED`

#### 4. `StudentProfile`
- **Identifier:** `studentId` (String, Required)
- **Properties:**
  - `studentId`: String — Required
  - `bloodGroup`: String — Optional
  - `nationality`: String — Optional
  - `dateOfBirth`: Date / String (ISO-8601 `YYYY-MM-DD`) — Optional
  - `email`: String — Optional
- **Verification Status:** `VERIFIED`

#### 5. `Guardian`
- **Identifier:** `guardianId` (String, Required)
- **Properties:**
  - `guardianId`: String — Required
  - `studentId`: String (Foreign Key reference) — Required
  - `guardianName`: String — Required
  - `relation`: String — Optional
  - `phoneNo`: String — Optional
  - `emailId`: String — Optional
- **Verification Status:** `VERIFIED`

#### 6. `Application`
- **Identifier:** `applicationId` (String, Required)
- **Properties:**
  - `applicationId`: String (e.g., `'APP001'`) — Required
  - `studentId`: String — Required (used to create `[:SUBMITTED]`)
  - `applicationDate`: Date / String (ISO-8601) — Optional (defaults to current date if omitted)
  - `applicationStatus`: String — Required. Allowed values: `{'Pending', 'Approved', 'Rejected'}`.
- **Verification Status:** `VERIFIED`

#### 7. `Scholarship`
- **Identifier:** `scholarshipId` (String, Required)
- **Properties:**
  - `scholarshipId`: String (e.g., `'SCH001'`) — Required
  - `applicationId`: String — Required (used to create `[:AWARDS]`)
  - `scholarshipType`: String — Required
  - `amount`: Float / Integer (Finite, Non-negative, e.g., `50000.0`) — Required
- **Verification Status:** `VERIFIED`

### B. Financial Entities (Member 3 Primary Domain / Schema Alignment)

The following properties are defined in Member 2's allowlist for schema consistency across team members:

| Label | Properties Defined in Allowlist | Expected Types | Status |
| :--- | :--- | :--- | :--- |
| `BankAccount` | `accountNo`, `bankName`, `ifsc`, `accountType` | All String | `NEEDS CONFIRMATION` from Member 3 |
| `Disbursement` | `disbursementId`, `scholarshipId`, `accountNo`, `disbursementDate`, `amount`, `disbursementMode` | Strings; `amount`: Float/Int; `disbursementDate`: Date | `NEEDS CONFIRMATION` from Member 3 |
| `Fee` | `feeId`, `studentId`, `feeAmount`, `dueDate` | Strings; `feeAmount`: Float/Int; `dueDate`: Date | `NEEDS CONFIRMATION` from Member 3 |
| `PaymentMethod` | `methodId`, `methodName` | String | `NEEDS CONFIRMATION` from Member 3 |
| `Payment` | `paymentId`, `feeId`, `scholarshipId`, `methodId`, `paymentDate`, `amountPaid`, `transactionId` | Strings; `amountPaid`: Float/Int; `paymentDate`: Date | `NEEDS CONFIRMATION` from Member 3 |

---

## 4. Graph Relationships and Directions

Member 2's backend relies directly on the following Cypher graph traversal patterns. Relationship names and directions **must** match Member 1's `03_create_relationships.cypher`:

| Source Node | Relationship Type | Target Node | Cypher Representation | Cardinality Assumption | Backend Operation Dependent on Pattern |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Department` | `HAS_PROGRAM` | `Program` | `(d:Department)-[:HAS_PROGRAM]->(p:Program)` | 1 to Many | `list_departments()`, `get_department()` |
| `Program` | `HAS_STUDENT` | `Student` | `(p:Program)-[:HAS_STUDENT]->(s:Student)` | 1 to Many | `list_students()`, `get_student()`, `create_student()`, `get_program_students()` |
| `Student` | `HAS_PROFILE` | `StudentProfile` | `(s:Student)-[:HAS_PROFILE]->(sp:StudentProfile)` | 1 to 1 | `get_student_profile()` |
| `Student` | `HAS_GUARDIAN` | `Guardian` | `(s:Student)-[:HAS_GUARDIAN]->(g:Guardian)` | 1 to Many | `get_student_guardians()` |
| `Student` | `SUBMITTED` | `Application` | `(s:Student)-[:SUBMITTED]->(a:Application)` | 1 to Many | `create_application()`, `get_application()`, `get_student_applications()` |
| `Application` | `AWARDS` | `Scholarship` | `(a:Application)-[:AWARDS]->(sch:Scholarship)` | 1 to 1 (Max 1) | `create_scholarship()`, `get_scholarship()`, `list_applications()` |
| `Scholarship` | `HAS_DISBURSEMENT` | `Disbursement` | `(sch:Scholarship)-[:HAS_DISBURSEMENT]->(d:Disbursement)` | 1 to Many | `get_scholarship()` (optional inspection) |
| `Disbursement` | `TO_ACCOUNT` | `BankAccount` | `(d:Disbursement)-[:TO_ACCOUNT]->(b:BankAccount)` | Many to 1 | Member 3 Financial Traversal |
| `Student` | `HAS_FEE` | `Fee` | `(s:Student)-[:HAS_FEE]->(f:Fee)` | 1 to Many | Member 3 Financial Traversal |
| `Fee` | `HAS_PAYMENT` | `Payment` | `(f:Fee)-[:HAS_PAYMENT]->(p:Payment)` | 1 to Many | Member 3 Financial Traversal |
| `Payment` | `PAID_VIA` | `PaymentMethod` | `(p:Payment)-[:PAID_VIA]->(m:PaymentMethod)` | Many to 1 | Member 3 Financial Traversal |
| `Payment` | `USES_SCHOLARSHIP` | `Scholarship` | `(p:Payment)-[:USES_SCHOLARSHIP]->(sch:Scholarship)` | Many to 0..1 | Member 3 Financial Traversal |

---

## 5. Critical Reconciliations & Discrepancies to Resolve

### Discrepancy: `SCH002` and `SCH004` Application Status in Sample Data
- **Location in Member 1 Script:** `database/neo4j/02_import_data.cypher`
- **Observed Data:**
  - `APP002` has `applicationStatus: 'Pending'`, yet `SCH002` (`Need Based Scholarship`, amount `30000`) awards it.
  - `APP004` has `applicationStatus: 'Rejected'`, yet `SCH004` (`Merit Scholarship`, amount `25000`) awards it.
- **Member 2 Business Rule Enforcement:**
  - `backend/graph_service.py` enforces in `create_scholarship()`:
    ```python
    if app_status != "Approved":
        raise ConflictError(
            f"Scholarships can only be awarded to approved applications. Current status: '{app_status}'."
        )
    ```
  - Any client attempting to create a new scholarship for a non-approved application receives an HTTP `409 Conflict`.
- **Impact & Action Needed:**
  - The sample data in `02_import_data.cypher` violates the academic business rule that scholarships can only be awarded upon approval.
  - While existing graph records imported from `02_import_data.cypher` remain readable via `GET /api/neo4j/scholarships` and `GET /api/neo4j/scholarships/<id>` without throwing errors, this inconsistency causes confusion in automated integration tests and query evaluations.
  - **Item for Member 1:** Reconcile `02_import_data.cypher` so that:
    1. Either `APP002` and `APP004` are set to `'Approved'`, OR
    2. `SCH002` and `SCH004` are removed or re-linked to other approved applications, OR
    3. The team officially documents that `SCH002` and `SCH004` are historical exception records.
  - *Status:* `NEEDS CONFIRMATION` from Member 1.

---

## 6. Compatibility Checks for Member 1's Migration Scripts

Before running `cypher-shell` against the live production or shared test container, Member 1 must verify:

1. **Date Serialization:** 
   Neo4j `Date` and `DateTime` objects created via `date('YYYY-MM-DD')` are supported by the backend via `clean_graph_item()`. Member 1 should ensure all date strings in `02_import_data.cypher` follow standard ISO-8601 `date('YYYY-MM-DD')` format.
2. **Constraint Verification:**
   Run `SHOW CONSTRAINTS` after executing `01_constraints.cypher` to ensure 12 UNIQUE constraints exist.
3. **Idempotency:**
   Ensure `02_import_data.cypher` uses `MERGE (n:Label {id: row.id})` and `03_create_relationships.cypher` uses `MERGE (a)-[:REL]->(b)` so running scripts multiple times does not duplicate nodes or edges.
4. **Referential Integrity:**
   Ensure no orphan nodes exist. Running `database/neo4j/04_verify_graph.cypher` must return 0 orphaned students or applications.

---

## 7. Sign-Off Checklist for Member 1 & Member 2

- [x] Node labels (12) and identifiers aligned
- [x] Relationship names (12) and directions verified
- [x] Date format ISO-8601 verified
- [ ] Application status discrepancy (`SCH002` / `SCH004`) resolved
- [ ] Migration executed on shared test container (pending user authorization)
