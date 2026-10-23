# Complete Codebase Analysis & Viva Preparation
# Deliverable 08: Business Rules and Code Review

**Project Title:** Scholarship and Fee Management System  
**Review Scope:** Financial Integrity, Constraints, Security Vulnerabilities, and Code Quality  
**Audited Files:** `database/*.sql`, `database/neo4j/*.cypher`, `backend/*.py`, `index.html`  
**Evidence Level:** `[VERIFIED]` directly from code inspection, schema constraints, and edge-case execution.

---

## 1. Domain & Financial Business Rules Inventory

The application enforces **10 core business and financial integrity rules**. The matrix below documents each rule, where it is implemented, how it is evaluated, and whether parity is maintained across both database engines.

| Rule # | Business Rule Statement | Implementation Layer & Code Location | Evaluation Timing | Behavior on Violation | Cross-Engine Parity Status |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **BR-1** | **Application Status Whitelist:** Application status must be strictly `'Pending'`, `'Approved'`, or `'Rejected'`. | **Oracle:** `02_constraints.sql` (`chk_application_status`)<br>**Backend:** `app.py` (`update_application_status`)<br>**Neo4j:** `graph_service.py` (`_validate_properties`) | On insert or update | Rejected with `ORA-02290` (Oracle) or `HTTP 400 Bad Request` (Backend/Neo4j). | **Enforced in both.** |
| **BR-2** | **Approved Application Prerequisite:** A scholarship grant can only be created for an application with status `'Approved'`. | **Backend (Oracle API):** `app.py` line 428 (`if application[0] != "Approved"`)<br>**Backend (Neo4j API):** `graph_service.py` line 908 | Prior to inserting into `SCHOLARSHIP` | Aborts insertion, returns `HTTP 400 Bad Request` (`"Scholarship can only be created for an approved application"`). | **Enforced in both backends.** *(Note: Missing in raw Oracle DDL; see Inconsistencies).* |
| **BR-3** | **Single Scholarship per Application:** An application cannot be awarded more than one scholarship grant (1:1). | **Oracle:** `01_create_tables.sql` (`UNIQUE (ApplicationID)`)<br>**Neo4j:** `graph_service.py` line 913 (`MATCH (a)-[:AWARDS]->(existing)`) | On insert | `ORA-00001: unique constraint violated` (Oracle) or `ConflictError` / `HTTP 409` (Neo4j). | **Enforced in both.** |
| **BR-4** | **Non-Negative Financial Grants:** Scholarship amounts, fee amounts, payment amounts, and disbursement amounts must be $\ge 0$. | **Oracle:** `chk_scholarship_amount`, `chk_fee_amount`, `chk_payment_amount`, `chk_disbursement_amount`<br>**Neo4j:** `graph_service.py` scalar property validation | On DDL insert/update | `ORA-02290: check constraint violated` (Oracle) or `InvalidInputError` / `HTTP 400` (Neo4j). | **Enforced in both.** |
| **BR-5** | **Disbursement Mode Whitelist:** Disbursement mode must be strictly `'Bank Transfer'` or `'Direct Transfer'`. | **Oracle:** `02_constraints.sql` (`chk_disbursement_mode`)<br>**Backend:** `app.py` line 681<br>**Neo4j:** `graph_service.py` line 1682 | On disbursement creation | `ORA-02290` (Oracle) or `HTTP 400 Bad Request` (Backend). | **Enforced in both.** |
| **BR-6** | **Disbursement Upper Limit:** Total disbursements cannot exceed the total awarded scholarship amount. | **Backend (Neo4j):** `graph_service.py` line 1740 (`if (total_disbursed + amount) > total_scholarship`)<br>**Oracle:** Not enforced in DDL; relies on application logic. | Prior to creating disbursement | `HTTP 400 Bad Request` (`"Disbursement exceeds the total scholarship amount"`). | **Enforced in Neo4j; Inferred in Oracle backend.** |
| **BR-7** | **Fee Due Date Mandatory:** Every student fee invoice must have a non-null settlement due date. | **Oracle:** `01_create_tables.sql` (`DueDate DATE NOT NULL`) & `02_constraints.sql` (`chk_fee_due_date`)<br>**Neo4j:** `graph_service.py` required keys | On fee insertion | `ORA-01400: cannot insert NULL` or `HTTP 400 Bad Request`. | **Enforced in both.** |
| **BR-8** | **Overpayment Prevention (Core Financial Rule):** Cumulative fee payments cannot exceed the total assessed fee amount. | **Oracle:** PL/SQL Trigger `TRG_CHECK_FEE_PAYMENT`<br>**Neo4j:** `graph_service.py` line 1500 (`if (total_paid + amount_paid) > total_fee`)<br>**Frontend:** `index.html` `validateFeeAmounts()` | Before physical row/node insertion | **Oracle:** `RAISE_APPLICATION_ERROR(-20001, 'Payment exceeds the total fee amount.')`<br>**Neo4j:** `InvalidInputError` / `HTTP 400`. | **Enforced in both engines.** |
| **BR-9** | **Transaction ID Uniqueness:** Every payment transaction ID must be globally unique across all financial records. | **Oracle:** `01_create_tables.sql` (`UNIQUE (TransactionID)`)<br>**Neo4j:** `01_constraints.cypher` (`payment_paymentId_unique`) + property check | On insert | `ORA-00001: unique constraint violated` (Oracle) or `ConflictError` / `HTTP 409` (Neo4j). | **Enforced in both.** |
| **BR-10**| **Payment Method Uniqueness:** Payment method names must be unique (no duplicate `'UPI'` or `'Credit Card'`). | **Oracle:** `02_constraints.sql` (`uq_payment_method_name`)<br>**Neo4j:** `01_constraints.cypher` (`paymentMethod_methodId_unique`) | On insert | `ORA-00001: unique constraint violated` (Oracle) or `ConflictError` (Neo4j). | **Enforced in both.** |

---

## 2. Business Rule Inconsistencies & Data Anomalies

During our deep audit, the following discrepancies and edge cases were discovered in the project source files:

### Anomaly 1: Sample Data Violates Business Rule 2 in `03_sample_data.sql`
- **The Rule:** A scholarship can only be created for an application with status `'Approved'`.
- **The Violation:** In `database/03_sample_data.sql`:
  - Line 144 inserts `SCH002` referencing `APP002`, where `APP002` has `ApplicationStatus = 'Pending'`.
  - Line 154 inserts `SCH004` referencing `APP004`, where `APP004` has `ApplicationStatus = 'Rejected'`.
- **Why this occurred:** In `backend/app.py`, the Flask endpoint `POST /api/scholarships` correctly validates `ApplicationStatus == 'Approved'`. However, in the raw SQL script `03_sample_data.sql`, the data was inserted directly with SQL `INSERT` statements before the backend validation was implemented. Because there is no database-level CHECK constraint or trigger in Oracle enforcing application status upon scholarship insertion, the invalid records were committed to the database.
- **Viva Implication:** If an examiner asks whether the database alone prevents awarding scholarships to rejected applications, you must state: *"In the database schema, it is enforced via application logic in Flask and Cypher service transactions, but there is no Oracle DDL check constraint linking the two tables, which allowed raw sample data to contain pending/rejected awards."*

---

## 3. Security, Quality, and Vulnerability Audit

### A. SQL and Cypher Injection Assessment
- **Oracle SQL (`backend/app.py`):** **SECURE (`[VERIFIED]`).**
  All SQL queries with user input utilize Oracle bind variables (e.g. `:student_id`, `:fee_id`, `:status`) via dictionary parameter passing (`cursor.execute(sql, {"student_id": val})`). No raw Python f-strings or string concatenations (`+`, `%`) are used to interpolate user input into SQL commands.
- **Neo4j Cypher (`backend/graph_service.py`):** **SECURE (`[VERIFIED]`).**
  All Cypher statements pass user values via parameterized dictionaries (`session.run(query, sid=student_id, props=properties)`). In `get_graph_data()`, the only dynamic string interpolation is the node label (`f"MATCH (n:{label})"`), but this is strictly guarded by line 2063:
  ```python
  if label not in ALLOWED_PROPERTIES:
      raise InvalidInputError(f"Unsupported label filter '{label}'.")
  ```
  Because the label is validated against a static hardcoded set, Cypher injection via label interpolation is impossible.

---

### B. Concurrency & Race Conditions in Overpayment Checking

Both the Oracle trigger `TRG_CHECK_FEE_PAYMENT` and the Neo4j service `create_payment()` contain a classic database concurrency vulnerability:

```
[Time]     Transaction A (User 1)                    Transaction B (User 2)
  |        ----------------------                    ----------------------
  T1:      Checks current paid: ₹60,000 / ₹75,000   
  T2:                                                Checks current paid: ₹60,000 / ₹75,000
  T3:      Wants to pay: ₹10,000                     Wants to pay: ₹10,000
  T4:      Check: 60k + 10k <= 75k (PASSED)          Check: 60k + 10k <= 75k (PASSED)
  T5:      Inserts ₹10,000; Commits                  
  T6:                                                Inserts ₹10,000; Commits
  |
  v        FINAL RESULT: Student has paid ₹80,000 for a ₹75,000 fee! OVERPAYMENT OCCURRED!
```

- **In Oracle:** Because `TRG_CHECK_FEE_PAYMENT` does not issue a `SELECT ... FOR UPDATE` on `STUDENT_FEE`, two concurrent sessions can read the same uncommitted total, both pass the check, and simultaneously insert payments that together exceed the fee amount.
- **Remediation for Oracle:** Lock the parent row during payment insertion:
  ```sql
  SELECT FeeAmount INTO v_fee_amount
  FROM STUDENT_FEE
  WHERE FeeID = :NEW.FeeID
  FOR UPDATE; -- Acquires row-exclusive lock on fee record
  ```
- **Remediation for Neo4j:** In Cypher, execute a write-lock pattern on the `:Fee` node:
  ```cypher
  MATCH (f:Fee {feeId: $fee_id})
  SET f._lock = timestamp() -- Enforces write lock on Fee node
  WITH f
  OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
  ...
  ```

---

### C. Oracle Mutating Table Error (`ORA-04091`) Risk

In Oracle PL/SQL, a row-level trigger (`FOR EACH ROW`) on table `T` that executes a `SELECT` against table `T` can trigger `ORA-04091: table is mutating, trigger/function may not see it`.
- In `06_plsql.sql`, `TRG_CHECK_FEE_PAYMENT` is defined as `BEFORE INSERT ON FEE_PAYMENT FOR EACH ROW`, and inside its body it runs:
  ```sql
  SELECT NVL(SUM(AmountPaid), 0) INTO v_total_paid
  FROM FEE_PAYMENT WHERE FeeID = :NEW.FeeID;
  ```
- **Operational Reality:** In Oracle 23c, a single-row `INSERT INTO FEE_PAYMENT VALUES (...)` succeeds because the table is not considered mutating during simple single-tuple inserts. However, if an administrator executes a bulk insert:
  `INSERT INTO FEE_PAYMENT SELECT * FROM STAGING_PAYMENTS;`
  Oracle will immediately crash with `ORA-04091`.
- **Best Practice Fix:** Maintain a running column `AmountPaid` on `STUDENT_FEE`, updated atomically, or use a compound trigger (`FOR EACH ROW` stores IDs; `AFTER STATEMENT` aggregates and validates).

---

## 4. Prioritized Code Review Recommendations

| Priority | Issue / Risk | Location | Explanation | Practical Remediation |
| :---: | :--- | :--- | :--- | :--- |
| **P1 (High)** | Concurrency Race Condition in Overpayment | `database/06_plsql.sql` & `graph_service.py` | Simultaneous payments can bypass validation and overpay. | Add `FOR UPDATE` lock on `STUDENT_FEE` in Oracle; add write lock on `:Fee` node in Cypher. |
| **P2 (High)** | Default Hardcoded Passwords in Fallbacks | `backend/db.py` & `backend/neo4j_db.py` | Fallback credentials (`oracle`, `system`) exist in source files. | Remove default password strings from `os.getenv()`; require strict `.env` loading. |
| **P3 (Medium)** | Sample Data Violates Approval Rule | `database/03_sample_data.sql` | `SCH002` and `SCH004` reference non-approved applications. | Update sample data so all awarded scholarships reference `'Approved'` applications. |
| **P4 (Medium)** | Missing Authentication & Authorization | `backend/app.py` & `neo4j_routes.py` | All API endpoints are publicly accessible without JWT or sessions. | Integrate Flask-Login or JWT bearer tokens with student vs admin role guards. |
| **P5 (Low)** | Potential Mutating Table on Bulk Inserts | `database/06_plsql.sql` | Row-level trigger queries own table during insert. | Convert to an Oracle Compound Trigger or maintain aggregated totals on parent fee row. |
| **P6 (Low)** | Redundant Check Constraint | `database/02_constraints.sql` | `chk_fee_due_date` checks `DueDate IS NOT NULL`, but `01_create_tables.sql` already defined it `NOT NULL`. | Harmless redundancy, but can be cleaned for tidiness. |
