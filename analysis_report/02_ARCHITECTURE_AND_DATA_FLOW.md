# Complete Codebase Analysis & Viva Preparation
# Deliverable 02: Architecture and Data Flow

**Project Title:** Scholarship and Fee Management System  
**System Architecture:** Dual-Engine Comparative Web Architecture (Oracle Relational + Neo4j Graph)  
**Evidence Level:** `[VERIFIED]` from `app.py`, `db.py`, `neo4j_db.py`, `graph_service.py`, `neo4j_routes.py`, `docker-compose.yml`, and `index.html`.

---

## 1. High-Level Architectural Model

The Scholarship and Fee Management System implements a multi-tier, dual-database web architecture. The system allows academic and financial data to be queried and mutated across two fundamentally different database paradigms:
1. **Relational Database Management System (RDBMS):** Oracle Database 23c Free, queried via SQL and PL/SQL.
2. **Graph Database Management System (Graph DBMS):** Neo4j 5 Community Edition, queried via Cypher pattern matching.

Both database engines are unified beneath a single **Python Flask (WSGI)** backend server, which exposes RESTful JSON endpoints consumed by a single-page responsive web client.

```
+=======================================================================================================+
|                                        TIER 1: PRESENTATION TIER                                      |
|                                                                                                       |
|  index.html (Single-Page Application: HTML5, CSS3, ES6 JavaScript)                                    |
|  - Campus Entrance Experience (Vector SVG & CSS Animation)                                           |
|  - Workspace Sections: Overview, Student Directory, Fee Ledger, Scholarship Catalog                   |
|  - Interactive Graph Canvas: Cytoscape.js 3.28.1 (5 dynamic physics layouts)                          |
|  - Visual Analytics: Chart.js (Fee reconciliation, scholarship lifecycle)                            |
|  - Engine Switcher: Dynamic header toggle selecting Oracle (/api) or Neo4j (/api/neo4j)               |
+=======================================================================================================+
                                                    |
                                            HTTP / JSON (REST)
                                        Ports: 5000 (API) / 5500
                                                    |
                                                    v
+=======================================================================================================+
|                                    TIER 2: APPLICATION / BACKEND TIER                                 |
|                                                                                                       |
|  WSGI Application Entry Point: backend/app.py (Flask 3.1.3 / Gunicorn 26.2.0)                        |
|  - CORS Configuration: flask_cors.CORS (Configurable via CORS_ALLOWED_ORIGINS)                        |
|  - Static Web Delivery: Routes /app and /ui serve repo index.html                                     |
|  - Route Dispatcher: Direct routes (/api/...) + Blueprint mounting (neo4j_bp at /api/neo4j)           |
|                                                                                                       |
|  +---------------------------------------------+   +-----------------------------------------------+  |
|  |           ORACLE CONTROLLER LOGIC           |   |            NEO4J BLUEPRINT CONTROLLER         |  |
|  |           backend/app.py (/api/...)         |   |      backend/neo4j_routes.py (/api/neo4j/...) |  |
|  | - Direct route functions (18 endpoints)     |   | - Blueprint route handlers (38 endpoints)     |  |
|  | - JSON request payload extraction           |   | - HTTP status code translation (400, 404, 409)|  |
|  | - Explicit cursor lifecycle (conn.cursor()) |   | - Error propagation to client                 |  |
|  +----------------------+----------------------+   +-----------------------+-----------------------+  |
|                         |                                                  |                          |
|                         |                                                  v                          |
|                         |                          +-----------------------------------------------+  |
|                         |                          |               GRAPH SERVICE LAYER             |  |
|                         |                          |            backend/graph_service.py           |  |
|                         |                          | - ALLOWED_PROPERTIES Whitelisting             |  |
|                         |                          | - Domain rule validation (overpayment check)  |  |
|                         |                          | - Parameterized Cypher statement builder      |  |
|                         |                          | - Cytoscape graph serialization (nodes/edges) |  |
|                         |                          +-----------------------+-----------------------+  |
|                         |                                                  |                          |
|                         v                                                  v                          |
|  +---------------------------------------------+   +-----------------------------------------------+  |
|  |           ORACLE CONNECTION DRIVER          |   |            NEO4J CONNECTION DRIVER            |  |
|  |                backend/db.py                |   |              backend/neo4j_db.py              |  |
|  | - python-oracledb 26.0.0 (Thin Mode)        |   | - neo4j-python-driver 6.4.1 (Bolt Protocol)   |  |
|  | - oracledb.connect(user, password, dsn)     |   | - @lru_cache singleton GraphDatabase.driver() |  |
|  | - Environment: ORACLE_USER, DSN, PASSWORD   |   | - Session management: driver.session()        |  |
|  +---------------------------------------------+   +-----------------------------------------------+  |
+=======================================================================================================+
                          |                                                  |
                     TCP Port 1521                                      TCP Port 7687
                    Oracle Net (TNS)                                    Bolt Protocol
                          |                                                  |
                          v                                                  v
+================================================+ +====================================================+
|         TIER 3A: ORACLE RELATIONAL ENGINE      | |           TIER 3B: NEO4J GRAPH ENGINE              |
|                                                | |                                                    |
|  Container: oracle-free                        | | Container: scholarship-neo4j                       |
|  Image: gvenzl/oracle-free:23-slim-faststart   | | Image: neo4j:5.26-community                        |
|  Database PDB: FREEPDB1                        | | Database Name: neo4j                               |
|  Storage Engine: Relational Table Spaces       | | Storage Engine: Labeled Property Graph (LPG)       |
|  - 12 Tables (Normalized 3NF / BCNF)           | | - 12 Node Labels (54 Nodes loaded)                 |
|  - 5 Views (VW_STUDENT_ACADEMIC, etc.)         | | - 12 Relationship Types (55 Relationships loaded)  |
|  - Constraints (PK, FK, CHECK, UNIQUE)         | | - 12 Uniqueness Constraints (Schema enforcement)   |
|  - PL/SQL Engine (TRG_CHECK_FEE_PAYMENT)       | | - Index-Free Adjacency (Double-linked memory ptrs) |
+================================================+ +====================================================+
```

---

## 2. End-to-End Request and Data Flow

Every interaction follows a strictly traceable request-response pipeline. Here is the operational execution flow adapted directly from the code:

```
[User Action] Click "Make Payment" or "Save Student"
       |
       v
[Step 1: Frontend Event Handler] Form submit intercepted in index.html (e.g., feeForm.addEventListener)
       |
       v
[Step 2: Client Validation & Payload Assembly]
       - Validate inputs (non-negative numbers, phone formats, non-empty fields)
       - Determine active engine (currentEngine === 'neo4j' ? '/api/neo4j' : '/api')
       - Assemble JSON payload: JSON.stringify({ fee_id, amount_paid, payment_date, method_id, transaction_id })
       |
       v
[Step 3: Asynchronous HTTP Transmission]
       - window.fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
       |
       v
[Step 4: WSGI Web Server Routing (Flask / Gunicorn)]
       - Flask matches incoming URL route and HTTP method
       - Route Dispatch:
           * If URL starts with /api/neo4j/... -> delegated to neo4j_bp in neo4j_routes.py
           * If URL starts with /api/... -> routed to handler function in app.py
       |
       v
[Step 5: Backend Input Validation & Business Rule Verification]
       - Check for required JSON fields
       - Validate types and domain constraints:
           * If Oracle: Python checks presence of fields; queries application approval status if scholarship.
           * If Neo4j: graph_service.py verifies properties against ALLOWED_PROPERTIES whitelist.
           * Overpayment check: Queries fee amount vs total paid so far.
       |
       v
[Step 6: Driver Invocation & Session Management]
       - Oracle: conn = get_connection(); cursor = conn.cursor()
       - Neo4j: with get_driver().session(database=get_database_name()) as session:
       |
       v
[Step 7: Database Query Execution & Physical Storage Mutation]
       - Oracle: cursor.execute("INSERT INTO FEE_PAYMENT ...", bind_params)
           * Oracle PL/SQL Trigger TRG_CHECK_FEE_PAYMENT fires automatically BEFORE INSERT
           * Checks: IF v_total_paid + :NEW.AmountPaid > v_fee_amount -> RAISE_APPLICATION_ERROR(-20001)
           * conn.commit() or conn.rollback()
       - Neo4j: session.execute_write(tx_create_payment)
           * Cypher: MATCH (f:Fee {feeId: $fid}) CREATE (p:Payment $props) MERGE (f)-[:HAS_PAYMENT]->(p)
           * Bolt protocol manages atomic transaction commit
       |
       v
[Step 8: Result Serialization & Response Generation]
       - Convert database tuples / nodes / records into Python dictionary
       - flask.jsonify(data), status code (200 OK, 201 Created, 400 Bad Request, 409 Conflict)
       |
       v
[Step 9: HTTP Response Return]
       - JSON payload sent across wire to client browser
       |
       v
[Step 10: Frontend DOM & Visual Canvas Update]
       - index.html receives JSON response
       - Displays flash alert message (showMessage('Payment recorded successfully', false))
       - Renders updated tables (renderFeeRecords())
       - Updates summary metric cards (updateDashboard())
       - Re-renders responsive charts (updateCharts())
       - If on Graph tab: Cytoscape adds node/edge dynamically and updates layout
```

---

## 3. Component Details & Connection Inventory

### A. Database Connection Configurations

The following connection specifications are verified from `backend/db.py`, `backend/neo4j_db.py`, and `docker-compose.yml`. All actual secret passwords have been redacted.

| Parameter | Oracle Relational Database | Neo4j Graph Database |
| :--- | :--- | :--- |
| **Driver Package** | `oracledb==26.0.0` (Python) | `neo4j==6.4.1` (Python official driver) |
| **Driver Mode / Protocol** | Thin Mode (Pure Python TCP) / Oracle TNS | Bolt Protocol (`bolt://`) over TCP |
| **Host Machine Location** | Containerized (`oracle-free`) or Local | Containerized (`scholarship-neo4j`) or Local |
| **Host / IP Address** | `localhost` (default) or `127.0.0.1` | `localhost` (default) or `neo4j` (in Docker network) |
| **Port** | `1521` | `7687` (Bolt) / `7474` (HTTP Browser) |
| **Service / Database Name** | `FREEPDB1` (Pluggable Database) | `neo4j` (Default graph database) |
| **Username** | `system` | `neo4j` |
| **Password Env Variable** | `ORACLE_PASSWORD` (Fallback: `[REDACTED]`) | `NEO4J_PASSWORD` (Mandatory in `neo4j_db.py`) |
| **URI / DSN Env Variable** | `ORACLE_DSN` (Default: `localhost:1521/FREEPDB1`) | `NEO4J_URI` (Default: `bolt://localhost:7687`) |
| **User Env Variable** | `ORACLE_USER` (Default: `system`) | `NEO4J_USERNAME` (Default: `neo4j`) |
| **Database Name Env Var** | In DSN (`FREEPDB1`) | `NEO4J_DATABASE` (Default: `neo4j`) |

### B. Environment & Configuration Loading

1. **Oracle (`backend/db.py`):**
   ```python
   DB_USER = os.getenv("ORACLE_USER", "system")
   DB_PASSWORD = os.getenv("ORACLE_PASSWORD", "[REDACTED]")
   DB_DSN = os.getenv("ORACLE_DSN", "localhost:1521/FREEPDB1")
   ```
   Values are loaded directly from the operating system environment at module import time using standard `os.getenv()`.

2. **Neo4j (`backend/neo4j_db.py`):**
   ```python
   def _load_env_if_needed():
       if os.getenv("NEO4J_PASSWORD"):
           return
       # Explicitly searches local .env files in backend/, cwd, or module root
   ```
   If environment variables are not exported in the shell, `neo4j_db.py` proactively scans for `.env` files in three candidate directories, parses non-comment lines, and populates `os.environ` before driver instantiation.

---

## 4. Error Propagation and Exception Handling Architecture

The system enforces disciplined error propagation across all tiers:

```
+----------------------------------------------------------------------------------------------------+
|                                      ERROR PROPAGATION MATRIX                                      |
+---------------------------------------+---------------------+-------------------+------------------+
| Error Condition                       | Raised In           | Translated To     | HTTP Status Code |
+---------------------------------------+---------------------+-------------------+------------------+
| Missing required JSON field           | Flask Route         | JSON {"error":..} | 400 Bad Request  |
| Malformed non-numeric fee amount      | Flask / Service     | JSON {"error":..} | 400 Bad Request  |
| Student / Application / Fee not found | Flask / Service     | NotFoundError     | 404 Not Found    |
| Primary Key / Unique ID collision     | DB / Service        | ConflictError     | 409 Conflict     |
| Payment exceeds fee (Oracle Trigger)  | Oracle Trigger P4   | oracledb.Error    | 400 Bad Request  |
| Payment exceeds fee (Neo4j Service)   | graph_service.py    | InvalidInputError | 400 Bad Request  |
| Illegal property key (not in list)    | graph_service.py    | InvalidInputError | 400 Bad Request  |
| Database container offline / timeout  | oracledb / neo4j    | Neo4jError / Ex   | 503 Service Unav.|
| Internal unhandled runtime failure    | Python Runtime      | Exception         | 500 Server Error |
+---------------------------------------+---------------------+-------------------+------------------+
```

### Transaction & Connection Management Rules:
- **Oracle (`app.py`):**
  - Uses explicit `try...except...finally` blocks in every route.
  - Cursors are opened per request: `cursor = conn.cursor()`.
  - On success: `conn.commit()` is explicitly called.
  - On exception: `conn.rollback()` is called in the `except` block.
  - In `finally`: `cursor.close()` and `conn.close()` are unconditionally executed to prevent connection leaks.
- **Neo4j (`neo4j_db.py` & `graph_service.py`):**
  - Uses a singleton driver cached via `@lru_cache(maxsize=1)`.
  - Sessions are opened using Python context managers: `with driver.session(...) as session:`.
  - Mutations execute inside explicit transaction functions (`session.execute_write(tx_func)`), which automatically commit on return and roll back if any exception is raised.
  - Sessions are cleanly returned to the driver connection pool upon exiting the `with` block.

---

## 5. Deployment Topology & Container Boundaries

```
[DEVELOPER WORKSTATION / HOST MACHINE]
  |
  +-- [Host Native Process] Web Browser (Client)
  |     - Opens http://127.0.0.1:5000/app or http://127.0.0.1:5500
  |
  +-- [Host Native Process (Optional)] Flask Development Server
  |     - python app.py (Runs on host Python 3.12/3.14 on 127.0.0.1:5000)
  |
  +-- [DOCKER RUNTIME ENGINE]
        |
        +-- Container 1: scholarship-neo4j (Up & Verified)
        |     - Image: neo4j:community (v5.26)
        |     - Port Bindings: 0.0.0.0:7474 -> 7474, 0.0.0.0:7687 -> 7687
        |     - Volumes: neo4j_data (/data), neo4j_logs (/logs)
        |     - Status: Running continuously on local machine
        |
        +-- Container 2: oracle-free (Verified)
        |     - Image: gvenzl/oracle-free:23-slim-faststart
        |     - Port Binding: 0.0.0.0:1521 -> 1521
        |     - PDB: FREEPDB1
        |
        +-- Container 3: scholarship-backend (Prepared via docker-compose.yml)
              - Multi-stage Dockerfile (python:3.12-slim)
              - Gunicorn WSGI server running as unprivileged 'appuser'
              - Bound to 0.0.0.0:5000
```
