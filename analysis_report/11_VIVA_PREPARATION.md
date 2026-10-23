# Complete Codebase Analysis & Viva Preparation
# Deliverable 11: DBMS Viva Preparation Guide

**Project Title:** Scholarship and Fee Management System  
**Audience:** College Student preparing for university DBMS Viva / Practical Examination  
**Author:** Senior Software Engineer, Database Architect, and DBMS Viva Mentor  
**Scope:** Core Concepts, 40 In-Depth Viva Q&As, 9 Line-by-Line Code Walkthroughs, and a 5–7 Minute Demo Script.

---

## 1. Core DBMS & Engineering Concepts (Tied Directly to Project Code)

| Concept | Academic Definition | How It Is Used in this Specific Codebase | Direct Code Reference |
| :--- | :--- | :--- | :--- |
| **Relational Model** | Represents data as relations (tables) composed of tuples (rows) and attributes (columns). | 12 tables representing university departments, programs, students, fees, and payments. | `database/01_create_tables.sql` |
| **Primary Key (PK)** | An attribute (or minimal set of attributes) that uniquely identifies each tuple in a relation; cannot be NULL. | `StudentID` in `STUDENT`, `FeeID` in `STUDENT_FEE`, `PaymentID` in `FEE_PAYMENT`. | `01_create_tables.sql` L22, L105, L122 |
| **Foreign Key (FK)** | An attribute in one table that references the primary key of another, enforcing referential integrity. | `STUDENT.ProgramID` referencing `PROGRAM.ProgramID`; `FEE_PAYMENT.FeeID` referencing `STUDENT_FEE.FeeID`. | `01_create_tables.sql` L30, L129 |
| **Normalization** | Systematic decomposition of relations to eliminate insertion, update, and deletion anomalies. | Decomposed into 12 tables achieving 3NF / BCNF. Personal details moved to `STUDENT_PROFILE` (1:1). | `01_create_tables.sql` L35–44 |
| **SQL vs PL/SQL** | SQL is a declarative query language; PL/SQL is Oracle's procedural extension adding variables, loops, and branching. | SQL used for CRUD in `04_queries.sql` and `app.py`; PL/SQL used for triggers and procedures in `06_plsql.sql`. | `database/04_queries.sql` vs `06_plsql.sql` |
| **DDL, DML, DQL, TCL** | DDL (Define schema: `CREATE`), DML (Manipulate: `INSERT`), DQL (Query: `SELECT`), TCL (Transaction control: `COMMIT`, `ROLLBACK`). | DDL in `01_create_tables.sql`; DML in `03_sample_data.sql`; DQL in `04_queries.sql`; TCL in `app.py` (`conn.commit()`). | Throughout SQL files and `app.py` |
| **Joins & Aggregation** | Combining tuples across relations via predicate matching (`JOIN`); computing summaries (`SUM`, `COUNT`, `AVG`). | 4-table joins in Query 7; `NVL(SUM(AmountPaid), 0)` in Query 8 and View 3 to compute outstanding fee balances. | `database/04_queries.sql` L92–126 |
| **Database Trigger** | Stored PL/SQL block that fires automatically in response to a DML event (`INSERT`, `UPDATE`, `DELETE`). | `TRG_CHECK_FEE_PAYMENT` executes `BEFORE INSERT ON FEE_PAYMENT` to prevent total payments exceeding the fee. | `database/06_plsql.sql` L132–164 |
| **Transactions & ACID** | Atomicity, Consistency, Isolation, Durability. Group of operations executed as a single indivisible unit. | Python `try...except` issues `conn.commit()` on success and `conn.rollback()` on error to maintain consistency. | `backend/app.py` L132, L141 |
| **Python DB Drivers** | Native client libraries translating Python data types to wire-level database socket protocols. | `oracledb` 26.0.0 in Thin mode connecting to Oracle TNS; `neo4j` 6.4.1 connecting to Bolt protocol socket. | `backend/db.py` & `backend/neo4j_db.py` |
| **Cursors** | Memory control structure allocated by the database to process query result rows iteratively. | `cursor = conn.cursor()`; fetches rows via `cursor.fetchall()`; closed in `finally` block to prevent leaks. | `backend/app.py` L30, L52, L62 |
| **Graph Database** | Stores data as nodes (entities) and directed edges (relationships), providing Index-Free Adjacency. | 12 node labels (e.g. `:Student`, `:Fee`) and 12 relationship types (e.g. `[:HAS_FEE]`, `[:HAS_PAYMENT]`). | `database/neo4j/01_constraints.cypher` |
| **Cypher Query Language** | Declarative ASCII-art pattern matching language for graph databases. | `MATCH (s:Student)-[:HAS_FEE]->(f:Fee) RETURN s, f` used in `graph_service.py` to traverse multi-hop paths. | `backend/graph_service.py` L1160 |
| **Docker & Port Mapping** | Operating system virtualization isolating services; port forwarding maps container ports to host machine. | Port 1521 maps to Oracle container; Ports 7474/7687 map to Neo4j container; Port 5000 maps to Flask. | `docker-compose.yml` L10–12, L34–35 |
| **Test Automation** | Programmatic verification asserting that code satisfies business rules without regressions. | 168 automated tests in `tests/` verifying routes, edge cases, whitelisting, and live database constraints. | `tests/test_financial_service.py` |

---

## 2. 40 High-Probability DBMS Viva Questions and Answers

### Category 1: Project Overview & Architecture
1. **Q: What is the purpose of this project?**  
   *A:* It is a Scholarship and Fee Management System designed for higher education institutions to manage students, academic programs, scholarship applications and disbursements, and tuition fees with multi-channel payment reconciliation across dual relational (Oracle) and graph (Neo4j) database engines.
2. **Q: Why did you implement both Oracle and Neo4j?**  
   *A:* To evaluate and demonstrate the strengths of two distinct database paradigms: Oracle RDBMS provides mature tabular financial ledger accounting, DDL constraints, and database triggers; Neo4j Labeled Property Graph excels at interconnected network queries (such as student scholarship journeys and guardian family networks) using constant-time Index-Free Adjacency without costly multi-table joins.
3. **Q: What is the role of Flask in this architecture?**  
   *A:* Flask acts as the unified middleware and API gateway. It receives HTTP requests from the frontend, handles input validation and domain checks, routes queries to either Oracle via `oracledb` or Neo4j via `neo4j`, serializes query results into standard JSON, and returns consistent HTTP status codes.
4. **Q: What web server is used in production versus development?**  
   *A:* In development, Flask's built-in Werkzeug development server is run via `python app.py`. In production, the application uses **Gunicorn 26.2.0** with 2 worker processes and a 120-second timeout, as defined in `Dockerfile` and `Procfile`.

### Category 2: Relational Schema & Normalization
5. **Q: How many tables are there in the Oracle database? Name them.**  
   *A:* Exactly 12 tables: `DEPARTMENT`, `PROGRAM`, `STUDENT`, `STUDENT_PROFILE`, `GUARDIAN`, `SCHOLARSHIP_APPLICATION`, `SCHOLARSHIP`, `BANK_ACCOUNT`, `DISBURSEMENT`, `STUDENT_FEE`, `PAYMENT_METHOD`, and `FEE_PAYMENT`.
6. **Q: What normal form is the database in, and why?**  
   *A:* It is in **Third Normal Form (3NF) and BCNF**. All attributes are atomic (1NF); all non-key attributes depend on the entire primary key because all primary keys are single-column (2NF); and there are no transitive dependencies (3NF) because program and department information are segregated into independent lookup relations rather than duplicated on each student tuple.
7. **Q: Why is `STUDENT_PROFILE` separated from `STUDENT`?**  
   *A:* It separates operational academic enrollment data (name, phone, address, program) from personal demographic data (blood group, nationality, DOB, email) in a clean 1:1 relation. This improves query efficiency for academic listings and allows strict access control over sensitive personal data.
8. **Q: What is the relationship between `SCHOLARSHIP_APPLICATION` and `SCHOLARSHIP`?**  
   *A:* It is a **1:1 relationship**. In `SCHOLARSHIP`, `ApplicationID` has a `UNIQUE` constraint in `01_create_tables.sql`. This ensures an application can be awarded at most one scholarship grant.

### Category 3: SQL & PL/SQL Deep Dive
9. **Q: How do you prevent cumulative payments from exceeding a student's fee amount?**  
   *A:* In Oracle, by a row-level `BEFORE INSERT` trigger named `TRG_CHECK_FEE_PAYMENT` on `FEE_PAYMENT`. It queries `STUDENT_FEE` for `FeeAmount` and sums existing payments from `FEE_PAYMENT`. If `v_total_paid + :NEW.AmountPaid > v_fee_amount`, it calls `RAISE_APPLICATION_ERROR(-20001, 'Payment exceeds the total fee amount.')`.
10. **Q: What is the mutating table error in Oracle (`ORA-04091`), and does your trigger risk it?**  
    *A:* `ORA-04091` occurs when a row-level trigger on table $T$ queries or modifies table $T$ while it is in the middle of being changed. In our trigger, it queries `FEE_PAYMENT` inside `BEFORE INSERT ON FEE_PAYMENT FOR EACH ROW`. In Oracle 23c, single-row inserts succeed without mutating errors, but a multi-row bulk insert (`INSERT INTO ... SELECT`) would trigger `ORA-04091`. The production remedy is to use an Oracle Compound Trigger or maintain a running total column on `STUDENT_FEE`.
11. **Q: What is the difference between `P_STUDENT_FEE_STATUS` and `F_OUTSTANDING_FEE`?**  
    *A:* `P_STUDENT_FEE_STATUS` is a **stored procedure** that prints a formatted text report to the terminal using `DBMS_OUTPUT.PUT_LINE`. `F_OUTSTANDING_FEE` is a **stored function** that returns a numeric value (`NUMBER(10,2)`), allowing it to be called directly inside SQL `SELECT` queries.
12. **Q: Explain how Query 9 calculates outstanding fees for every student.**  
    *A:* Query 9 performs a `LEFT JOIN` between `STUDENT_FEE` and `FEE_PAYMENT` grouped by `StudentID`, `FeeAmount`. It uses `NVL(SUM(fp.AmountPaid), 0)` to handle students who have made zero payments (converting NULL to 0), and computes `sf.FeeAmount - NVL(SUM(fp.AmountPaid), 0) AS OutstandingAmount`.
13. **Q: Why are Database Views used in this project? Name two.**  
    *A:* Views simplify complex joins, provide modularity, and secure underlying table structures. For example, `VW_STUDENT_ACADEMIC` pre-joins students, programs, and departments; and `VW_PENDING_APPLICATIONS` isolates applications with `ApplicationStatus = 'Pending'` for administrative reviews.

### Category 4: Flask & Python Backend
14. **Q: How does Flask connect to Oracle Database?**  
    *A:* Using the `oracledb` library in `backend/db.py`. The function `get_connection()` calls `oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)`.
15. **Q: What is a Flask Blueprint, and why did you use it?**  
    *A:* A Blueprint (`neo4j_bp` in `backend/neo4j_routes.py`) organizes a group of related routes, handlers, and error translators into a modular component mounted under a specific URL prefix (`/api/neo4j`), completely isolating Neo4j routes from Oracle routes.
16. **Q: How do you prevent SQL Injection in your Flask routes?**  
    *A:* By using parameterized queries with named bind variables (e.g. `:student_id`, `:fee_id`). The query string and user parameters are passed separately to `cursor.execute(sql, {"student_id": val})`, ensuring user input is treated strictly as data, never as executable SQL.
17. **Q: How are database transactions handled in Flask?**  
    *A:* In `backend/app.py`, every mutating route wraps execution in `try...except`. On successful execution, `conn.commit()` is called. If an error occurs, `conn.rollback()` executes in the `except` block. In the `finally` block, `cursor.close()` and `conn.close()` are unconditionally executed to avoid connection leaks.

### Category 5: Neo4j & Cypher
18. **Q: What is Index-Free Adjacency in Neo4j?**  
    *A:* In relational databases, traversing a relationship requires searching a B-Tree index ($O(\log N)$) or computing hash tables. In Neo4j, each node physically stores direct in-memory double-linked pointers to its connected neighbor nodes. Traversing an edge is a constant-time ($O(1)$) pointer dereference, independent of total database size.
19. **Q: How are foreign keys represented in Neo4j?**  
    *A:* Foreign keys are replaced with **first-class directed relationships** (edges). For example, rather than storing `programId` in a student record, the graph materializes `(p:Program)-[:HAS_STUDENT]->(s:Student)`.
20. **Q: What unique constraints did you create in Neo4j?**  
    *A:* We created 12 schema uniqueness constraints in `01_constraints.cypher` enforcing that canonical identifiers (`studentId`, `feeId`, `paymentId`, etc.) cannot be duplicated across nodes with that label.
21. **Q: Explain how your Cypher query prevents Cartesian multiplication when calculating fees.**  
    *A:* In `05_graph_queries.cypher` (Query 3), we use independent subqueries via `CALL { WITH fee ... }`. One subquery aggregates `sum(payment.amountPaid)` strictly per fee, while a separate subquery collects payment method strings, preventing an $M \times N$ row multiplication.
22. **Q: How does `get_graph_data()` format graph elements for the frontend?**  
    *A:* It compiles nodes into `{"data": {"id": elem_id, "label": "Student", "caption": "...", "color": "#3b82f6"}}` and edges into `{"data": {"source": src_id, "target": tgt_id, "label": "HAS_FEE"}}`. This conforms exactly to the JSON data schema expected by **Cytoscape.js**.

### Category 6: Frontend & Cytoscape.js
23. **Q: How does the frontend switch between Oracle and Neo4j?**  
    *A:* The top navigation bar contains `#engineSelector`. When changed, `switchEngine()` updates the variable `currentEngine`. The central helper `fetchAPI(endpoint)` checks `currentEngine`: if set to `'neo4j'`, it prefixes `/api/neo4j`; otherwise, it uses `/api`.
24. **Q: What is Cytoscape.js, and what layouts does your application support?**  
    *A:* Cytoscape.js is a client-side JavaScript graph visualization library. Our application supports 5 layouts: **COSE** (force-directed spring simulation), **Concentric** (radial hierarchy), **Breadthfirst** (hierarchical tree), **Circle**, and **Grid**.
25. **Q: What is an Ego-Network in your graph visualization?**  
    *A:* An ego-network isolates a single central entity ("ego") and its immediate neighborhood. In preset "Aarav Sharma (S001) Ego Network", Cypher matches `(s:Student {studentId: 'S001'})-[*1..3]-(m)`, displaying all academic and financial records within 3 hops of S001.

### Category 7: Business Rules & Financial Integrity
26. **Q: Can a student pay more than their outstanding fee?**  
    *A:* No. Both engines strictly reject overpayment. In Oracle, trigger `TRG_CHECK_FEE_PAYMENT` raises `-20001`. In Neo4j, `create_payment()` in `graph_service.py` checks `if (total_paid + amount_paid) > total_fee:` and raises `InvalidInputError` with HTTP 400.
27. **Q: Can a scholarship be awarded to a rejected application?**  
    *A:* In the Flask backend (`POST /api/scholarships`), it is strictly rejected with `HTTP 400: "Scholarship can only be created for an approved application"`. However, in raw sample data (`03_sample_data.sql`), records were inserted directly in SQL before backend validation was written.
28. **Q: What are the allowed disbursement modes?**  
    *A:* Exactly two: `'Bank Transfer'` and `'Direct Transfer'`, enforced by check constraint `chk_disbursement_mode` in Oracle and whitelisted in `graph_service.py`.

### Category 8: Docker & Deployment
29. **Q: What Docker containers are used in this project?**  
    *A:* Two primary database containers: `oracle-free` (Oracle 23c Free on port 1521) and `scholarship-neo4j` (Neo4j 5.26 Community on ports 7474 and 7687). In production, a third container `scholarship-backend` runs Gunicorn.
30. **Q: Why does the Dockerfile use a multi-stage build?**  
    *A:* Stage 1 (`builder`) installs compilers and builds wheels. Stage 2 (`runner`) copies only the compiled packages into a lean Python 3.12-slim image, drops build tools, and runs as an unprivileged user `appuser` to minimize security attack vectors and reduce image size.
31. **Q: Is the application currently deployed to a public cloud URL?**  
    *A:* Local containerized deployment is 100% verified. Cloud deployment on Render is fully configured via `render.yaml` and `Dockerfile`, but is not live on a public URL because provisioning external cloud hosting requires personal user account credentials and billing setup.

### Category 9: Testing & Quality Assurance
32. **Q: How many tests are there, and did they pass?**  
    *A:* There are **168 automated tests** across 8 test suites in `tests/`. All 168 tests pass with a 100% success rate in 0.97 seconds.
33. **Q: Do your tests pollute or destroy live database data?**  
    *A:* No. 164 unit tests use `unittest.mock` to simulate database responses. The 4 live integration tests in `test_neo4j_live.py` generate dynamic hex UUID identifiers (e.g. `TEST_S_A1B2C3D4`) and issue `DETACH DELETE` on those specific UUIDs in `tearDown()`, leaving the shared database 100% pristine.

### Category 10: Limitations & Engineering Fixes
34. **Q: What is a race condition, and could it affect your payment trigger?**  
    *A:* A race condition occurs when two concurrent transactions read the same data before either commits. If two payments of ₹10,000 are submitted simultaneously for a ₹15,000 balance, both read existing total ₹0, both pass validation, and ₹20,000 is committed. The fix is row-exclusive locking: `SELECT FeeAmount FROM STUDENT_FEE WHERE FeeID = :id FOR UPDATE;`.
35. **Q: Do Oracle and Neo4j stay synchronized automatically in real time?**  
    *A:* No. They are implemented as independent comparative data stores loaded from identical baseline scripts. There is no real-time dual-write distributed transaction (2PC) or Change Data Capture (CDC) pipeline.
36. **Q: Why is authentication missing in the API?**  
    *A:* The application was developed as an academic demonstration of database architectures. For production, JWT bearer token authentication or session-based RBAC (Role-Based Access Control) should be added to secure endpoints.
37. **Q: What happens if the Neo4j container crashes?**  
    *A:* The backend catches `neo4j.exceptions.ServiceUnavailable`, logs the failure, and returns a clean `HTTP 503 Service Unavailable` JSON response instead of crashing the Flask server.
38. **Q: What is the purpose of the `.gitignore` file?**  
    *A:* It excludes virtual environments (`venv/`), Python byte-cache (`__pycache__/`, `*.pyc`), and local environment credential files (`.env`) from being accidentally committed to version control.
39. **Q: What is the DSN in `backend/db.py`?**  
    *A:* Data Source Name: `localhost:1521/FREEPDB1`. It specifies the host machine (`localhost`), standard Oracle listener port (`1521`), and Pluggable Database service name (`FREEPDB1`).
40. **Q: If an examiner asks you to demonstrate a feature that fails, what should you do?**  
    *A:* Explain the architectural failure mode with confidence: check whether the target Docker container is running (`docker ps`), explain the error propagation from driver to Flask HTTP status code, and point to the corresponding automated test case that validates the scenario.

---

## 3. Practical Line-by-Line Code Walkthroughs

### Walkthrough 1: Oracle PL/SQL Overpayment Trigger (`database/06_plsql.sql`)
```sql
132: CREATE OR REPLACE TRIGGER TRG_CHECK_FEE_PAYMENT
133: BEFORE INSERT ON FEE_PAYMENT
134: FOR EACH ROW
135: DECLARE
136:     v_fee_amount STUDENT_FEE.FeeAmount%TYPE;
137:     v_total_paid NUMBER(10,2);
138: BEGIN
139:     SELECT FeeAmount INTO v_fee_amount
140:     FROM STUDENT_FEE WHERE FeeID = :NEW.FeeID;
141:
142:     SELECT NVL(SUM(AmountPaid), 0) INTO v_total_paid
143:     FROM FEE_PAYMENT WHERE FeeID = :NEW.FeeID;
144:
145:     IF v_total_paid + :NEW.AmountPaid > v_fee_amount THEN
146:         RAISE_APPLICATION_ERROR(-20001, 'Payment exceeds the total fee amount.');
147:     END IF;
148: EXCEPTION
149:     WHEN NO_DATA_FOUND THEN
150:         RAISE_APPLICATION_ERROR(-20002, 'Fee record does not exist.');
151: END;
```
- **Line 132–134:** Declares a row-level `BEFORE INSERT` trigger on `FEE_PAYMENT`. `FOR EACH ROW` means it fires once for every tuple being inserted.
- **Line 136:** `v_fee_amount STUDENT_FEE.FeeAmount%TYPE`: Anchored type declaration ensuring variable matches column type dynamically.
- **Line 139–140:** Queries the parent fee record using `:NEW.FeeID` (the foreign key on the row being inserted).
- **Line 142–143:** Computes current cumulative payments using `NVL(SUM(AmountPaid), 0)`.
- **Line 145–147:** Evaluates the domain rule: if cumulative plus new amount exceeds total fee, aborts insertion and raises Oracle user-defined error `-20001`.
- **Line 149–150:** Traps missing fee parent records, raising error `-20002`.

---

### Walkthrough 2: Neo4j Transactional Overpayment Check (`backend/graph_service.py`)
```python
1471: def tx_create_payment(tx):
1472:     fee_check = tx.run("""
1473:         MATCH (f:Fee {feeId: $fee_id})
1474:         OPTIONAL MATCH (f)-[:HAS_PAYMENT]->(p:Payment)
1475:         RETURN f.feeAmount AS total_fee, coalesce(sum(p.amountPaid), 0) AS total_paid
1476:     """, fee_id=fee_id).single()
1477:
1478:     if not fee_check:
1479:         raise NotFoundError(f"Fee '{fee_id}' does not exist.")
1480:
1481:     total_fee = float(fee_check["total_fee"])
1482:     total_paid = float(fee_check["total_paid"])
1483:
1484:     if (total_paid + amount_paid) > total_fee:
1485:         raise InvalidInputError("Payment exceeds the total fee amount.")
```
- **Line 1471:** Python function passed to `session.execute_write(tx_create_payment)` for managed transactional execution.
- **Line 1472–1476:** Runs parameterized Cypher to fetch `total_fee` and sum existing payments using `coalesce()` (Cypher's equivalent to SQL `NVL`).
- **Line 1484–1485:** Enforces exact parity with the Oracle trigger: raises `InvalidInputError` if overpayment is detected, triggering an automatic rollback of the Bolt transaction.

---

## 4. 5–7 Minute Live Viva Demonstration Script

Follow this structured script when presenting the project to examiners:

### Minute 1: Introduction & Architecture Setup
- *"Good morning/afternoon. Today I am presenting the Scholarship and Fee Management System. This project manages student enrollment, scholarship workflows, and tuition fee reconciliation."*
- *"A key engineering highlight of this project is its comparative Dual-Engine Architecture: it unifies a traditional Relational Database (Oracle Database 23c Free) and a Labeled Property Graph Database (Neo4j 5 Community) beneath a single Flask WSGI backend."*

### Minute 2: Campus Portal & Student Directory
- Open browser to `http://127.0.0.1:5000/app`.
- Point out the entrance animation: *"We implemented an illustrated campus entrance screen with CSS student animations. Clicking 'Enter Dashboard' transitions to the management workspace."*
- Click **Students** in sidebar: *"Here is our student directory. The top bar shows our active database engine: Oracle Database Free. Notice how searching 'Aarav' filters records in real time."*

### Minute 3: Financial Fee Ledger & Overpayment Prevention
- Click **Fee Records** in sidebar.
- Point to student `S001`: *"Student S001 has an assessed tuition fee of ₹75,000, with ₹35,000 paid to date, leaving an outstanding balance of ₹40,000."*
- Demonstrate the financial rule: *"Watch what happens if I attempt to record a payment of ₹50,000 for S001."*
- Click submit: Red error banner appears: `Payment exceeds the total fee amount.`
- Explain: *"This is enforced at the database level by Oracle PL/SQL trigger `TRG_CHECK_FEE_PAYMENT`. It calculates existing payments plus the new amount and calls `RAISE_APPLICATION_ERROR(-20001)`. The Flask backend intercepts this and returns HTTP 400."*

### Minute 4: Switch to Neo4j Graph Database
- In top navigation bar, change `#engineSelector` from *Oracle* to **Neo4j Graph Database (/api/neo4j)**.
- Point to badge: *"Notice the indicator badge changes to 'Active Database: Neo4j Graph Database'. All subsequent network requests are now routed through our Flask Blueprint to Neo4j via the Bolt protocol."*

### Minute 5: Cytoscape.js Interactive Graph Explorer
- Click **Neo4j Graph Explorer** tab.
- Cytoscape canvas renders 54 nodes and 55 relationships.
- Select preset **"Aarav Sharma (S001) Ego Network"**:
  - *"Here is the multi-hop ego-network for Aarav Sharma, executed via Cypher traversal up to 3 hops without table joins."*
  - *"Blue nodes represent Students, red nodes represent Fees, teal nodes represent Payments, and gold stars represent Scholarships."*
  - Click on node `S001`: Side panel displays key-value properties and incoming/outgoing edges.
  - Switch layout from **COSE** to **Concentric**: Physics layout recalculates live on canvas.

### Minute 6: Automated Testing & Code Quality Evidence
- Switch to terminal:
  ```bash
  pytest
  ```
- Point to output: *"Our entire application is backed by an automated regression suite of 168 tests across 8 modules, passing in under one second. This includes 4 live integration tests that execute against our running Neo4j Docker container."*

### Minute 7: Conclusion & Summary
- *"In conclusion, this project demonstrates that relational databases excel at structured ledger transactions, while graph databases provide superior query expressiveness and constant-time traversal for interconnected academic networks. I am now ready to answer any questions."*
