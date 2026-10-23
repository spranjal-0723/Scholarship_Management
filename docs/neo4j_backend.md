# Scholarship and Fee Management System — DA-3 Neo4j Backend Documentation

## 1. Overview and Architecture

In DA-3, the Scholarship and Fee Management System adopts a dual-database architecture:
- **Oracle Database Free (Relational Backend):** Preserves the complete DA-2 relational schema, PL/SQL procedures, triggers, constraints, views, and 19 REST endpoints in `backend/app.py`.
- **Neo4j Graph Database (Graph Backend):** Introduces a property graph backend to model academic hierarchies, scholarship applications, and fee flows as interconnected nodes and relationships.
- **Flask REST Layer:** Exposes the backend via unified Flask routing. The Neo4j functionality is cleanly modularized as a Flask Blueprint (`neo4j_bp`) registered with the prefix `/api/neo4j`.

```text
                           CLIENT (Browser / Postman / Member 3 UI)
                                            |
                                            v
                                +-----------------------+
                                |      FLASK APP        |
                                |   (backend/app.py)    |
                                +-----------+-----------+
                                            |
                         +------------------+------------------+
                         |                                     |
                         v                                     v
                 Oracle Routes                         Neo4j Blueprint
              (19 @app.route APIs)                   (/api/neo4j/* routes)
                         |                                     |
                  python-oracledb                           neo4j 6.4.1
                         |                                     |
                         v                                     v
                 ORACLE FREE DB                        NEO4J GRAPH DB
               (Local Docker / PDB)               (scholarship-neo4j container)
```

---

## 2. Neo4j Configuration and Startup

### Docker Setup
The Neo4j database runs in a dedicated Docker container:
- **Container Name:** `scholarship-neo4j`
- **Docker Image:** `neo4j:community`
- **Volume:** `scholarship-neo4j-data`
- **Exposed Ports:**
  - `7474`: Neo4j Browser (HTTP)
  - `7687`: Bolt protocol

### Environment Variables
Environment configuration is isolated in `backend/.env` (which is excluded from Git via `.gitignore`). A safe template with placeholder values is provided in `backend/.env.example`:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=replace_with_local_password
NEO4J_DATABASE=neo4j
```

### Driver Lifecycle (`backend/neo4j_db.py`)
- The Neo4j Python driver is initialized via `neo4j.GraphDatabase.driver`.
- It is cached as a singleton using `@lru_cache(maxsize=1)` to prevent socket leaks and connection overhead.
- Environment variables are automatically loaded from `backend/.env` if not already exported in the shell environment.
- Connectivity verification is handled by `verify_connection()`, which executes `RETURN 1 AS result`. Any connection failure raises a sanitised `RuntimeError` that prevents credential disclosure in error logs.

---

## 3. Registered API Endpoints

The Neo4j Blueprint (`neo4j_bp`) exposes the following endpoints:

### Academic Endpoints (Member 2 Scope)
| Method | Endpoint | Description | Query / Body Parameters |
|---|---|---|---|
| `GET` | `/api/neo4j/health` | Health check for Neo4j connectivity | None |
| `GET` | `/api/neo4j/students` | List students with program and department | `limit` (int, default: 100, max: 500) |
| `GET` | `/api/neo4j/students/<student_id>` | Detailed student information | None |
| `POST` | `/api/neo4j/students` | Create student (links to Program if provided) | JSON: `studentId`, `studentName`, `phone`, optional properties |
| `GET` | `/api/neo4j/students/<student_id>/profile` | Get student profile via `HAS_PROFILE` | None |
| `GET` | `/api/neo4j/students/<student_id>/guardians` | Get student guardians via `HAS_GUARDIAN` | None |
| `GET` | `/api/neo4j/departments` | List departments with program counts | None |
| `GET` | `/api/neo4j/departments/<dept_id>` | Get department and programs via `HAS_PROGRAM` | None |
| `GET` | `/api/neo4j/programs` | List programs with department info | None |
| `GET` | `/api/neo4j/programs/<program_id>/students` | Get students enrolled via `HAS_STUDENT` | None |
| `GET` | `/api/neo4j/applications` | List applications (supports `?status=...`) | `status` (optional), `limit` (int) |
| `GET` | `/api/neo4j/applications/<application_id>` | Get application with student and scholarship | None |
| `POST` | `/api/neo4j/applications` | Create application (links via `SUBMITTED`) | JSON: `applicationId`, `studentId`, optional `applicationStatus` |
| `PUT` | `/api/neo4j/applications/<application_id>/status` | Update status (`Pending`, `Approved`, `Rejected`) | JSON: `{"status": "..."}` |
| `GET` | `/api/neo4j/students/<student_id>/applications` | Get applications for a student | None |
| `GET` | `/api/neo4j/scholarships` | List scholarships with application info | `limit` (int) |
| `GET` | `/api/neo4j/scholarships/<scholarship_id>` | Get scholarship with application & disbursements | None |
| `POST` | `/api/neo4j/scholarships` | Create scholarship (enforces Approved & 1:1) | JSON: `scholarshipId`, `applicationId`, `scholarshipType`, `amount` |

### Generic Foundation Endpoints
| Method | Endpoint | Description | Query / Body Parameters |
|---|---|---|---|
| `GET` | `/api/neo4j/nodes/<label>` | List nodes of an allowlisted label | `limit` (int, default: 100, range: 1–500) |
| `GET` | `/api/neo4j/nodes/<label>/<identifier>` | Retrieve a single node by its primary identifier | None |
| `POST` | `/api/neo4j/nodes/<label>` | Create a node of an allowlisted label | JSON object containing properties + identifier |

---

## 4. Academic Business Rules & Constraints

1. **Status Domain Enforcement:**
   Application status values must be strictly one of `{'Pending', 'Approved', 'Rejected'}`.
2. **Scholarship Award Prerequisite:**
   New scholarships can only be created for applications that are in `Approved` status. Creating a scholarship for a `Pending` or `Rejected` application fails with `409 Conflict`.
3. **Cardinality (1:1 Application-to-Scholarship):**
   An application can have at most one scholarship. Attempting to award a second scholarship to an application returns `409 Conflict`.
4. **Referential Integrity:**
   - Creating an Application requires an existing Student.
   - Creating a Student with a `programId` requires an existing Program.
   - Creating a Scholarship requires an existing Application.
5. **Non-negative Numeric Amounts:**
   Scholarship `amount` must be numeric, finite, and non-negative (`amount >= 0`).
6. **Property Whitelisting:**
   Requests with unsupported property keys are rejected with `400 Bad Request`.

---

## 5. Request and Response Examples

### 5.1 Create Student
```http
POST /api/neo4j/students HTTP/1.1
Content-Type: application/json

{
  "studentId": "S101",
  "studentName": "Kavya Menon",
  "phone": "9876543299",
  "programId": "P01",
  "city": "Chennai"
}
```
**Response (201 Created):**
```json
{
  "student": {
    "city": "Chennai",
    "phone": "9876543299",
    "programId": "P01",
    "studentId": "S101",
    "studentName": "Kavya Menon"
  }
}
```

### 5.2 Create Application
```http
POST /api/neo4j/applications HTTP/1.1
Content-Type: application/json

{
  "applicationId": "APP101",
  "studentId": "S101",
  "applicationStatus": "Pending"
}
```
**Response (201 Created):**
```json
{
  "application": {
    "applicationId": "APP101",
    "applicationStatus": "Pending",
    "studentId": "S101"
  }
}
```

### 5.3 Update Application Status
```http
PUT /api/neo4j/applications/APP101/status HTTP/1.1
Content-Type: application/json

{
  "status": "Approved"
}
```
**Response (200 OK):**
```json
{
  "application": {
    "applicationId": "APP101",
    "applicationStatus": "Approved",
    "studentId": "S101"
  }
}
```

### 5.4 Create Scholarship
```http
POST /api/neo4j/scholarships HTTP/1.1
Content-Type: application/json

{
  "scholarshipId": "SCH101",
  "applicationId": "APP101",
  "scholarshipType": "Merit Scholarship",
  "amount": 50000.0
}
```
**Response (201 Created):**
```json
{
  "scholarship": {
    "amount": 50000.0,
    "applicationId": "APP101",
    "scholarshipId": "SCH101",
    "scholarshipType": "Merit Scholarship"
  }
}
```

---

## 6. HTTP Error Codes & Strategy

- **`200 OK`**: Successful read or update.
- **`201 Created`**: Successful entity creation.
- **`400 Bad Request`**: Validation error (invalid label, non-integer limit, negative amount, missing mandatory field, unsupported property).
- **`404 Not Found`**: Resource does not exist in graph.
- **`409 Conflict`**: Duplicate primary identifier or business rule conflict (e.g. unapproved application or application already awarded a scholarship).
- **`500 Internal Server Error`**: Unexpected service error. Stack traces and internals are masked.
- **`503 Service Unavailable`**: Downstream Neo4j database unreachable or query timeout.

---

## 7. Automated Test Suite

```text
tests/
├── test_academic_service.py   # 29 tests: Student, App, Scholarship CRUD and business rules
├── test_academic_routes.py    # 25 tests: Flask test client routes for academic endpoints
├── test_graph_service.py      # 13 tests: Generic CRUD validation and constraint translation
├── test_neo4j_routes.py       # 21 tests: Generic /nodes routes and health check
├── test_app_integration.py    # 3 tests: Oracle route preservation and Neo4j route map check
└── test_neo4j_live.py         # 3 tests: Live container integration tests with cleanup
```

**Verification Commands:**
```bash
# Run entire test suite
backend/venv/bin/pytest -v

# Or run via unittest
backend/venv/bin/python -m unittest discover -s tests -v
```

**Results:**
- **94 Total Tests:** 94 Passed, 0 Failed, 0 Skipped (0.87s runtime).
- Live Neo4j database verified clean (0 residual nodes).
