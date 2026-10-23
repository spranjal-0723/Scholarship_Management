# Complete Codebase Analysis & Viva Preparation
# Deliverable 03: Oracle SQL and PL/SQL Deep Dive

**Project Title:** Scholarship and Fee Management System  
**Database Engine:** Oracle Database 23c Free (`gvenzl/oracle-free:23-slim-faststart`)  
**Pluggable Database (PDB):** `FREEPDB1`  
**Connection Driver:** `oracledb` 26.0.0 (Thin Mode)  
**Evidence Level:** `[VERIFIED]` directly from `database/01_create_tables.sql` through `database/06_plsql.sql`, `backend/db.py`, and `backend/app.py`.

---

## 1. Relational Schema and Table Specifications

The relational schema consists of exactly **12 normalized tables**. The tables were created using DDL in `01_create_tables.sql` and augmented with business constraints in `02_constraints.sql`.

```
                                  +------------------+
                                  |    DEPARTMENT    |
                                  +--------+---------+
                                           | 1
                                           | HAS_PROGRAM
                                           | N
                                  +--------v---------+
                                  |     PROGRAM      |
                                  +--------+---------+
                                           | 1
                                           | ENROLLED_IN
                                           | N
                                  +--------v---------+
                      +----------->|     STUDENT      |<-----------+
                      |           +---+----+-----+---+            |
                      | 1             | 1  | 1   | 1              | 1
                      | HAS_PROFILE   |    |     |                | HAS_GUARDIAN
                      | 1             |    |     |                | N
             +--------v--------+      |    |     |       +--------v--------+
             | STUDENT_PROFILE |      |    |     |       |    GUARDIAN     |
             +-----------------+      |    |     |       +-----------------+
                                      |    |     |
                         SUBMITTED_BY |    |     | ASSESSED_FOR
                                    1 |    |     | 1
             +------------------------v-+  |  +--v---------------------+
             | SCHOLARSHIP_APPLICATION  |  |  |      STUDENT_FEE       |
             +------------+-------------+  |  +-----------+-----------+
                          | 1              |              | 1
                          | AWARDS         |              | PAID_FOR
                          | 1 (UNIQUE)     |              | N
             +------------v-------------+  |  +-----------v-----------+
             |       SCHOLARSHIP        |<-+  |      FEE_PAYMENT      |
             +------------+-------------+ (opt| (USES_SCH)            |
                          | 1                 +-----------+-----------+
                          | HAS_DISBURSEMENT              | N
                          | N                             | PAID_VIA
             +------------v-------------+                 | 1
             |       DISBURSEMENT       |     +-----------v-----------+
             +------------+-------------+     |    PAYMENT_METHOD     |
                          | N                 +-----------------------+
                          | DEPOSITED_TO
                          | 1
             +------------v-------------+
             |       BANK_ACCOUNT       |
             +--------------------------+
```

---

### Detailed Table Specifications

#### 1. `DEPARTMENT`
- **Purpose:** Represents the top-level academic division (e.g., Computer Science, Electronics, Mechanical Engineering).
- **Columns:**
  - `DeptID VARCHAR2(10)`: Primary Key. Department code (e.g., `'D01'`).
  - `DeptName VARCHAR2(100)`: NOT NULL. Full department title.
- **Constraints:** `PRIMARY KEY (DeptID)`.
- **Relationships:** Referenced by `PROGRAM.DeptID` (1:N).

#### 2. `PROGRAM`
- **Purpose:** Represents academic degree programs offered by departments.
- **Columns:**
  - `ProgramID VARCHAR2(10)`: Primary Key. Unique program code (e.g., `'P01'`).
  - `ProgramName VARCHAR2(100)`: NOT NULL. Full name of the degree.
  - `DegreeLevel VARCHAR2(20)`: NOT NULL. Qualification level (e.g., `'BTech'`).
  - `DeptID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `DEPARTMENT(DeptID)`.
- **Constraints:** `PRIMARY KEY (ProgramID)`, `CONSTRAINT fk_program_department FOREIGN KEY (DeptID) REFERENCES DEPARTMENT(DeptID)`.
- **Relationships:** Belongs to one `DEPARTMENT`; referenced by `STUDENT.ProgramID` (1:N).

#### 3. `STUDENT`
- **Purpose:** Stores core identity, contact, address, and academic program enrollment.
- **Columns:**
  - `StudentID VARCHAR2(10)`: Primary Key. Unique identifier (e.g., `'S001'`).
  - `StudentName VARCHAR2(100)`: NOT NULL. Student's legal name.
  - `Phone VARCHAR2(15)`: NOT NULL. Contact phone number.
  - `HouseNo VARCHAR2(20)`: Optional street address component.
  - `Street VARCHAR2(100)`: Optional street name.
  - `City VARCHAR2(50)`: Optional city of residence.
  - `PIN VARCHAR2(10)`: Optional postal code.
  - `ProgramID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `PROGRAM(ProgramID)`.
- **Constraints:** `PRIMARY KEY (StudentID)`, `CONSTRAINT fk_student_program FOREIGN KEY (ProgramID) REFERENCES PROGRAM(ProgramID)`.
- **Relationships:** Enrolled in one `PROGRAM`; referenced by `STUDENT_PROFILE` (1:1), `GUARDIAN` (1:N), `SCHOLARSHIP_APPLICATION` (1:N), and `STUDENT_FEE` (1:N).

#### 4. `STUDENT_PROFILE`
- **Purpose:** Isolates personal and demographic attributes from core enrollment, achieving clean 1:1 normalization.
- **Columns:**
  - `StudentID VARCHAR2(10)`: Primary Key and Foreign Key referencing `STUDENT(StudentID)`.
  - `BloodGroup VARCHAR2(5)`: Optional blood group (e.g., `'O+'`, `'A+'`).
  - `Nationality VARCHAR2(50)`: Optional nationality (e.g., `'Indian'`).
  - `DateOfBirth DATE`: Optional date of birth.
  - `Email VARCHAR2(100)`: Optional personal email.
- **Constraints:** `PRIMARY KEY (StudentID)`, `CONSTRAINT fk_profile_student FOREIGN KEY (StudentID) REFERENCES STUDENT(StudentID)`.
- **Relationships:** Strict 1:1 child extension of `STUDENT`.

#### 5. `GUARDIAN`
- **Purpose:** Tracks parent or legal guardian details for each student.
- **Columns:**
  - `GuardianID VARCHAR2(10)`: Primary Key (e.g., `'G001'`).
  - `StudentID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `STUDENT(StudentID)`.
  - `GuardianName VARCHAR2(100)`: NOT NULL. Legal name of guardian.
  - `Relation VARCHAR2(30)`: Relationship to student (e.g., `'Father'`, `'Mother'`).
  - `PhoneNo VARCHAR2(15)`: Contact number.
  - `EmailID VARCHAR2(100)`: Contact email.
- **Constraints:** `PRIMARY KEY (GuardianID)`, `CONSTRAINT fk_guardian_student FOREIGN KEY (StudentID) REFERENCES STUDENT(StudentID)`.
- **Relationships:** Many-to-one (N:1) with `STUDENT`.

#### 6. `SCHOLARSHIP_APPLICATION`
- **Purpose:** Records student submissions for financial assistance and their review status.
- **Columns:**
  - `ApplicationID VARCHAR2(10)`: Primary Key (e.g., `'APP001'`).
  - `StudentID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `STUDENT(StudentID)`.
  - `ApplicationDate DATE`: NOT NULL. Date submission occurred.
  - `ApplicationStatus VARCHAR2(20)`: NOT NULL. Current workflow status.
- **Constraints:** 
  - `PRIMARY KEY (ApplicationID)`
  - `CONSTRAINT fk_application_student FOREIGN KEY (StudentID) REFERENCES STUDENT(StudentID)`
  - Added in `02_constraints.sql`: `CONSTRAINT chk_application_status CHECK (ApplicationStatus IN ('Pending', 'Approved', 'Rejected'))`.
- **Relationships:** Submitted by `STUDENT` (N:1); referenced by `SCHOLARSHIP` (1:1).

#### 7. `SCHOLARSHIP`
- **Purpose:** Represents the financial grant awarded to an approved application.
- **Columns:**
  - `ScholarshipID VARCHAR2(10)`: Primary Key (e.g., `'SCH001'`).
  - `ApplicationID VARCHAR2(10)`: NOT NULL and UNIQUE. Foreign Key referencing `SCHOLARSHIP_APPLICATION(ApplicationID)`.
  - `ScholarshipType VARCHAR2(50)`: NOT NULL. Category (e.g., `'Merit Scholarship'`).
  - `Amount NUMBER(10,2)`: NOT NULL. Grant value in INR.
- **Constraints:** 
  - `PRIMARY KEY (ScholarshipID)`
  - `UNIQUE (ApplicationID)` (Enforces that an application cannot be awarded more than one scholarship grant).
  - `CONSTRAINT fk_scholarship_application FOREIGN KEY (ApplicationID) REFERENCES SCHOLARSHIP_APPLICATION(ApplicationID)`
  - `CONSTRAINT chk_scholarship_amount CHECK (Amount >= 0)`.
- **Relationships:** Linked 1:1 to `SCHOLARSHIP_APPLICATION`; referenced by `DISBURSEMENT` (1:N) and optionally by `FEE_PAYMENT` (1:N).

#### 8. `BANK_ACCOUNT`
- **Purpose:** Stores verified institutional or student bank account details for direct electronic fund disbursement.
- **Columns:**
  - `AccountNo VARCHAR2(20)`: Primary Key (e.g., `'AC001'`).
  - `BankName VARCHAR2(100)`: NOT NULL. Financial institution name.
  - `IFSC VARCHAR2(20)`: NOT NULL. Indian Financial System Code.
  - `AccountType VARCHAR2(30)`: NOT NULL. Account classification (e.g., `'Savings'`).
- **Constraints:** `PRIMARY KEY (AccountNo)`.
- **Relationships:** Referenced by `DISBURSEMENT.AccountNo` (1:N).

#### 9. `DISBURSEMENT`
- **Purpose:** Records actual financial tranches paid out against an awarded scholarship into a bank account.
- **Columns:**
  - `DisbursementID VARCHAR2(10)`: Primary Key (e.g., `'DIS001'`).
  - `ScholarshipID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `SCHOLARSHIP(ScholarshipID)`.
  - `AccountNo VARCHAR2(20)`: NOT NULL. Foreign Key referencing `BANK_ACCOUNT(AccountNo)`.
  - `DisbursementDate DATE`: NOT NULL. Transfer execution date.
  - `Amount NUMBER(10,2)`: NOT NULL. Transferred tranche amount.
  - `DisbursementMode VARCHAR2(30)`: NOT NULL. Payment rail.
- **Constraints:** 
  - `PRIMARY KEY (DisbursementID)`
  - `CONSTRAINT fk_disbursement_scholarship FOREIGN KEY (ScholarshipID) REFERENCES SCHOLARSHIP(ScholarshipID)`
  - `CONSTRAINT fk_disbursement_account FOREIGN KEY (AccountNo) REFERENCES BANK_ACCOUNT(AccountNo)`
  - `CONSTRAINT chk_disbursement_amount CHECK (Amount >= 0)`
  - Added in `02_constraints.sql`: `CONSTRAINT chk_disbursement_mode CHECK (DisbursementMode IN ('Bank Transfer', 'Direct Transfer'))`.

#### 10. `STUDENT_FEE`
- **Purpose:** Represents the semester or annual tuition fee invoice assessed against a student.
- **Columns:**
  - `FeeID VARCHAR2(10)`: Primary Key (e.g., `'F001'`).
  - `StudentID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `STUDENT(StudentID)`.
  - `FeeAmount NUMBER(10,2)`: NOT NULL. Total assessed tuition amount.
  - `DueDate DATE`: NOT NULL. Mandatory settlement deadline.
- **Constraints:** 
  - `PRIMARY KEY (FeeID)`
  - `CONSTRAINT fk_fee_student FOREIGN KEY (StudentID) REFERENCES STUDENT(StudentID)`
  - `CONSTRAINT chk_fee_amount CHECK (FeeAmount >= 0)`
  - Added in `02_constraints.sql`: `CONSTRAINT chk_fee_due_date CHECK (DueDate IS NOT NULL)`.
- **Relationships:** Assessed for `STUDENT` (N:1); referenced by `FEE_PAYMENT` (1:N).

#### 11. `PAYMENT_METHOD`
- **Purpose:** Canonical lookup table of accepted payment instruments.
- **Columns:**
  - `MethodID VARCHAR2(10)`: Primary Key (e.g., `'M01'`).
  - `MethodName VARCHAR2(50)`: NOT NULL. Instrument name (e.g., `'UPI'`, `'Net Banking'`, `'Credit Card'`).
- **Constraints:** 
  - `PRIMARY KEY (MethodID)`
  - Added in `02_constraints.sql`: `CONSTRAINT uq_payment_method_name UNIQUE (MethodName)`.
- **Relationships:** Referenced by `FEE_PAYMENT.MethodID` (1:N).

#### 12. `FEE_PAYMENT`
- **Purpose:** Ledger recording every individual transaction paid toward settling a student fee.
- **Columns:**
  - `PaymentID VARCHAR2(10)`: Primary Key (e.g., `'PAY001'`).
  - `FeeID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `STUDENT_FEE(FeeID)`.
  - `ScholarshipID VARCHAR2(10)`: Optional NULLABLE Foreign Key referencing `SCHOLARSHIP(ScholarshipID)`. Populated if the payment was funded via institutional scholarship adjustment.
  - `MethodID VARCHAR2(10)`: NOT NULL. Foreign Key referencing `PAYMENT_METHOD(MethodID)`.
  - `PaymentDate DATE`: NOT NULL. Timestamp of settlement.
  - `AmountPaid NUMBER(10,2)`: NOT NULL. Payment value.
  - `TransactionID VARCHAR2(30)`: NOT NULL and UNIQUE. External gateway reference.
- **Constraints:** 
  - `PRIMARY KEY (PaymentID)`
  - `UNIQUE (TransactionID)`
  - `CONSTRAINT fk_payment_fee FOREIGN KEY (FeeID) REFERENCES STUDENT_FEE(FeeID)`
  - `CONSTRAINT fk_payment_scholarship FOREIGN KEY (ScholarshipID) REFERENCES SCHOLARSHIP(ScholarshipID)`
  - `CONSTRAINT fk_payment_method FOREIGN KEY (MethodID) REFERENCES PAYMENT_METHOD(MethodID)`
  - `CONSTRAINT chk_payment_amount CHECK (AmountPaid >= 0)`.

---

## 2. Normalization Audit (1NF through BCNF)

The relational schema demonstrates rigorous adherence to database normalization principles:

1. **First Normal Form (1NF):**
   - All attributes contain strictly atomic, scalar values (e.g. `Phone` stores a single number; address fields are decomposed into `HouseNo`, `Street`, `City`, `PIN`).
   - Every relation has a defined Primary Key.
   - There are no repeating groups or multi-valued arrays.
2. **Second Normal Form (2NF):**
   - Meets 1NF.
   - All primary keys are single-column identifiers (e.g., `StudentID`, `FeeID`, `PaymentID`).
   - Therefore, no partial functional dependencies ($X \rightarrow Y$ where $X \subset \text{PK}$) can mathematically exist. Every non-key attribute depends on the *whole* primary key.
3. **Third Normal Form (3NF):**
   - Meets 2NF.
   - There are no transitive dependencies ($X \rightarrow Y \rightarrow Z$).
   - For example, student address does not store department information; program details (`ProgramName`, `DegreeLevel`) are factored out into `PROGRAM` rather than repeated across every student tuple. Department names reside solely in `DEPARTMENT`.
4. **Boyce-Codd Normal Form (BCNF):**
   - Meets 3NF.
   - For every non-trivial functional dependency $X \rightarrow Y$, $X$ is a superkey (candidate key).
   - In `SCHOLARSHIP`, `ApplicationID` is unique, making both `ScholarshipID` and `ApplicationID` valid candidate keys.

---

## 3. SQL Query Catalog Deep Dive (`database/04_queries.sql`)

The project implements **20 production SQL queries** demonstrating joins, aggregation, grouping, subqueries, and analytical reporting:

| Query ID | Business Objective | SQL Operations Utilized | Tables Read | Output Produced |
| :--- | :--- | :--- | :--- | :--- |
| **Q1** | Student academic directory | 3-Table Inner Join (`STUDENT`, `PROGRAM`, `DEPARTMENT`), `ORDER BY` | `STUDENT`, `PROGRAM`, `DEPARTMENT` | Student ID, Name, Program Name, Dept Name |
| **Q2** | Student demographic profile | 1:1 Inner Join on `StudentID` | `STUDENT`, `STUDENT_PROFILE` | Blood group, nationality, DOB, email |
| **Q3** | Scholarship applications | Inner Join on `StudentID`, `ORDER BY ApplicationDate` | `SCHOLARSHIP_APPLICATION`, `STUDENT` | Application ID, student name, date, status |
| **Q4** | Approved scholarships & values | 3-Table Join, `WHERE ApplicationStatus = 'Approved'`, `ORDER BY Amount DESC` | `STUDENT`, `SCHOLARSHIP_APPLICATION`, `SCHOLARSHIP` | Student details, scholarship type, amount |
| **Q5** | Scholarship category metrics | Group by category, Aggregate functions: `COUNT(*)`, `SUM(Amount)`, `AVG(Amount)` | `SCHOLARSHIP` | Count, total sum, and average grant per type |
| **Q6** | Above-average fee students | Correlated/Scalar Subquery: `WHERE FeeAmount > (SELECT AVG(FeeAmount) FROM STUDENT_FEE)` | `STUDENT`, `STUDENT_FEE` | Students paying higher-than-average tuition |
| **Q7** | Fee payment transaction audit | 4-Table Join connecting payment to fee, student, and payment method | `FEE_PAYMENT`, `STUDENT_FEE`, `STUDENT`, `PAYMENT_METHOD` | Payment ID, Fee ID, student, method, amount |
| **Q8** | Total fee paid per student | `LEFT JOIN` on `FEE_PAYMENT`, `GROUP BY`, `NVL(SUM(AmountPaid), 0)` | `STUDENT`, `STUDENT_FEE`, `FEE_PAYMENT` | Student ID, fee assessed, total paid to date |
| **Q9** | Outstanding fee per student | `LEFT JOIN`, `GROUP BY`, Arithmetic calculation: `FeeAmount - NVL(SUM(AmountPaid), 0)` | `STUDENT`, `STUDENT_FEE`, `FEE_PAYMENT` | Real-time outstanding balances |
| **Q10** | Scholarship disbursements | 5-Table Join connecting disbursement to scholarship, application, student, and bank | `DISBURSEMENT`, `SCHOLARSHIP`, `SCHOLARSHIP_APPLICATION`, `STUDENT`, `BANK_ACCOUNT` | Full audit trail of disbursed funds & target bank |
| **Q11** | Department enrollment headcount | Double `LEFT JOIN`, `GROUP BY DeptID, DeptName`, `COUNT(s.StudentID)` | `DEPARTMENT`, `PROGRAM`, `STUDENT` | Student count per academic department |
| **Q12** | Pending applications filter | Simple Join with filter `WHERE ApplicationStatus = 'Pending'` | `SCHOLARSHIP_APPLICATION`, `STUDENT` | List of unreviewed applications |
| **Q13** | Student with highest grant | Subquery maximum: `WHERE Amount = (SELECT MAX(Amount) FROM SCHOLARSHIP)` | `STUDENT`, `SCHOLARSHIP_APPLICATION`, `SCHOLARSHIP` | Top scholarship recipient record |
| **Q14** | Bank disbursement volume | `JOIN`, `GROUP BY BankName`, `COUNT(DisbursementID)`, `SUM(Amount)` | `BANK_ACCOUNT`, `DISBURSEMENT` | Total tranches and monetary volume per bank |
| **Q15** | Frequent fee payers | `JOIN`, `GROUP BY StudentID`, `HAVING COUNT(PaymentID) > 1` | `STUDENT`, `STUDENT_FEE`, `FEE_PAYMENT` | Students who split tuition into multiple installments |
| **Q16** | Guardian emergency contact list | Inner Join on `StudentID` | `GUARDIAN`, `STUDENT` | Guardian name, relation, phone, student name |
| **Q17** | Total approved scholarship sum | Filtered Join, `SUM(Amount)`, `WHERE ApplicationStatus = 'Approved'` | `SCHOLARSHIP`, `SCHOLARSHIP_APPLICATION` | Gross institutional scholarship liability |
| **Q18** | Defaulter list (Outstanding > 0) | `LEFT JOIN`, `GROUP BY`, `HAVING FeeAmount - NVL(SUM(AmountPaid), 0) > 0` | `STUDENT`, `STUDENT_FEE`, `FEE_PAYMENT` | Students with remaining unpaid fee balances |
| **Q19** | Undisbursed scholarships | `LEFT JOIN DISBURSEMENT`, `WHERE d.DisbursementID IS NULL` | `SCHOLARSHIP_APPLICATION`, `STUDENT`, `SCHOLARSHIP`, `DISBURSEMENT` | Scholarships awarded but not yet paid out |
| **Q20** | Gateway channel performance | `LEFT JOIN FEE_PAYMENT`, `GROUP BY MethodName`, `NVL(SUM(AmountPaid), 0)` | `PAYMENT_METHOD`, `FEE_PAYMENT` | Total revenue collected via UPI, NetBanking, etc. |

---

## 4. Database Views Analysis (`database/05_views.sql`)

Views provide abstraction, simplify complex client joins, and secure underlying table structures:

1. **`VW_STUDENT_ACADEMIC`:**
   - Joins `STUDENT`, `PROGRAM`, and `DEPARTMENT`.
   - Simplifies retrieving a student's full academic context in a single query without manually joining 3 tables.
2. **`VW_SCHOLARSHIP_APPLICATION`:**
   - Joins `SCHOLARSHIP_APPLICATION`, `STUDENT`, and `LEFT JOIN SCHOLARSHIP`.
   - Returns application status alongside awarded scholarship amount (or NULL if unawarded/pending).
3. **`VW_STUDENT_FEE_SUMMARY`:**
   - Joins `STUDENT`, `STUDENT_FEE`, and `LEFT JOIN FEE_PAYMENT`.
   - Groups by fee record and calculates `TotalPaid` and `OutstandingAmount` using `NVL(SUM(fp.AmountPaid), 0)`.
4. **`VW_DISBURSEMENT_DETAILS`:**
   - Joins `DISBURSEMENT`, `SCHOLARSHIP`, `SCHOLARSHIP_APPLICATION`, `STUDENT`, and `BANK_ACCOUNT`.
   - Produces a comprehensive banking audit trail for every disbursed payment.
5. **`VW_PENDING_APPLICATIONS`:**
   - Filters `SCHOLARSHIP_APPLICATION` where `ApplicationStatus = 'Pending'`.
   - Dedicated administrative view for scholarship review committees.

---

## 5. PL/SQL Implementation Deep Dive (`database/06_plsql.sql`)

PL/SQL extends Oracle SQL with procedural capabilities, variables, conditional logic, exception handlers, explicit cursors, and row-level database triggers.

### A. Stored Procedure: `P_STUDENT_FEE_STATUS`
- **Definition:** `CREATE OR REPLACE PROCEDURE P_STUDENT_FEE_STATUS (p_student_id IN STUDENT.StudentID%TYPE)`
- **Purpose:** Looks up a student's fee amount, calculates total payments made, computes the net outstanding balance, and outputs a formatted report using `DBMS_OUTPUT.PUT_LINE`.
- **Logic:**
  ```sql
  SELECT s.StudentName, sf.FeeAmount
  INTO v_student_name, v_fee_amount
  FROM STUDENT s JOIN STUDENT_FEE sf ON s.StudentID = sf.StudentID
  WHERE s.StudentID = p_student_id;

  SELECT NVL(SUM(AmountPaid), 0)
  INTO v_total_paid
  FROM FEE_PAYMENT fp JOIN STUDENT_FEE sf ON fp.FeeID = sf.FeeID
  WHERE sf.StudentID = p_student_id;

  v_outstanding := v_fee_amount - v_total_paid;
  ```
- **Exception Handling:** Traps `WHEN NO_DATA_FOUND` (prints error message) and `WHEN OTHERS` (prints `SQLERRM`).
- **Invocation:** Called manually in SQL*Plus / SQL Developer via `EXEC P_STUDENT_FEE_STATUS('S001');` or embedded in anonymous blocks.

### B. Stored Function: `F_OUTSTANDING_FEE`
- **Definition:** `CREATE OR REPLACE FUNCTION F_OUTSTANDING_FEE (p_fee_id IN STUDENT_FEE.FeeID%TYPE) RETURN NUMBER`
- **Purpose:** Programmatically returns the exact numeric outstanding balance for a given `FeeID`.
- **Return Value:** `NUMBER(10,2)` representing `v_fee_amount - v_total_paid`. Returns `NULL` if fee does not exist.
- **Why Function vs Procedure?** Functions return a direct value and can be embedded directly inside SQL statements (e.g. `SELECT FeeID, F_OUTSTANDING_FEE(FeeID) FROM STUDENT_FEE`).

### C. Stored Procedure with Explicit Cursor: `P_APPROVED_SCHOLARSHIPS`
- **Definition:** `CREATE OR REPLACE PROCEDURE P_APPROVED_SCHOLARSHIPS`
- **Purpose:** Iterates through all approved scholarships using an explicit cursor and prints each record.
- **Cursor Mechanism:**
  ```sql
  CURSOR c_scholarships IS
      SELECT s.StudentID, s.StudentName, sc.ScholarshipType, sc.Amount
      FROM STUDENT s
      JOIN SCHOLARSHIP_APPLICATION sa ON s.StudentID = sa.StudentID
      JOIN SCHOLARSHIP sc ON sa.ApplicationID = sc.ApplicationID
      WHERE sa.ApplicationStatus = 'Approved'
      ORDER BY sc.Amount DESC;

  BEGIN
      FOR r IN c_scholarships LOOP
          DBMS_OUTPUT.PUT_LINE(r.StudentID || ' | ' || r.StudentName || ' | ' || r.ScholarshipType || ' | ' || r.Amount);
      END LOOP;
  END;
  ```
- **Viva Note:** The cursor FOR loop is an Oracle optimization: it automatically opens the cursor, fetches records iteratively, and closes the cursor when done, eliminating cursor leak risks.

### D. Financial Overpayment Prevention Trigger: `TRG_CHECK_FEE_PAYMENT`
- **Definition:** `CREATE OR REPLACE TRIGGER TRG_CHECK_FEE_PAYMENT BEFORE INSERT ON FEE_PAYMENT FOR EACH ROW`
- **Type:** Row-level `BEFORE INSERT` trigger.
- **Purpose:** Ensures financial data integrity by blocking any payment transaction that would cause cumulative payments to exceed the assessed fee amount.
- **Execution Logic:**
  ```sql
  SELECT FeeAmount INTO v_fee_amount
  FROM STUDENT_FEE WHERE FeeID = :NEW.FeeID;

  SELECT NVL(SUM(AmountPaid), 0) INTO v_total_paid
  FROM FEE_PAYMENT WHERE FeeID = :NEW.FeeID;

  IF v_total_paid + :NEW.AmountPaid > v_fee_amount THEN
      RAISE_APPLICATION_ERROR(-20001, 'Payment exceeds the total fee amount.');
  END IF;
  ```
- **Exception Trap:** If the referenced fee does not exist, `WHEN NO_DATA_FOUND` raises `RAISE_APPLICATION_ERROR(-20002, 'Fee record does not exist.')`.
- **Execution Event:** Fires automatically inside the Oracle SQL engine immediately before any new row is physically written into `FEE_PAYMENT`.

---

## 6. Oracle Python Driver & Connectivity Architecture

### How Python Communicates with Oracle (`backend/db.py`)
1. **Driver Identification:**
   - Package: `oracledb` 26.0.0.
   - Operating Mode: **Thin Mode** (pure Python implementation of the Oracle Net protocol). Does not require the Oracle Instant Client C-libraries or `libclntsh.dylib`.
2. **DSN Assembly:**
   - Assembled as `localhost:1521/FREEPDB1`.
   - `localhost`: Target machine where Docker container publishes port.
   - `1521`: Standard Oracle TNS listener port.
   - `FREEPDB1`: Pluggable Database (PDB) name inside the Oracle 23c Free container.
3. **Connection Lifecycle in Flask Route (`backend/app.py`):**
   ```python
   conn = None
   cursor = None
   try:
       conn = get_connection()       # 1. Connects to Oracle via TCP
       cursor = conn.cursor()         # 2. Allocates cursor memory handle
       cursor.execute(sql, params)   # 3. Sends parameterized SQL over wire
       conn.commit()                  # 4. Explicit two-phase commit
   except Exception as e:
       if conn:
           conn.rollback()            # 5. Rollback on failure
       return jsonify({"error": str(e)}), 400
   finally:
       if cursor:
           cursor.close()             # 6. Release cursor resource
       if conn:
           conn.close()               # 7. Close socket / connection
   ```
4. **Step-by-Step Request Trace (`GET /api/students`):**
   - User navigates to Student Directory.
   - Browser sends `GET /api/students`.
   - `app.py` executes `get_students()`.
   - `db.py` calls `oracledb.connect(user="system", password="[REDACTED]", dsn="localhost:1521/FREEPDB1")`.
   - Oracle verifies authentication, binds session to `FREEPDB1`.
   - Cursor runs 3-table join (`STUDENT` + `PROGRAM` + `DEPARTMENT`).
   - Results fetched via `cursor.fetchall()`, zipped with column headers from `cursor.description`.
   - Flask returns JSON array of students (`HTTP 200 OK`).
   - `cursor.close()` and `conn.close()` terminate the session cleanly.
