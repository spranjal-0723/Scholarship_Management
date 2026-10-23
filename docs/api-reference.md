# REST API Reference Manual

**Scholarship and Fee Management System**  
**Backend Framework:** Python 3.11 / Flask 3.1  
**Default Base URL:** `http://127.0.0.1:5050`  
**Authentication Scheme:** Cookie-based Session (`HttpOnly`, `SameSite=Lax`) with CSRF Header Token (`X-CSRFToken`)

---

## Table of Contents
1. [Authentication & Security Endpoints](#1-authentication--security-endpoints)
2. [System Health & Diagnostics](#2-system-health--diagnostics)
3. [Oracle Core Business REST API](#3-oracle-core-business-rest-api)
   - [Dashboard Metrics](#dashboard-metrics)
   - [Students & Profiles](#students--profiles)
   - [Scholarship Applications & Awards](#scholarship-applications--awards)
   - [Disbursements & Bank Accounts](#disbursements--bank-accounts)
   - [Fees, Payments & Offset Validation](#fees-payments--offset-validation)
4. [Neo4j Graph Database REST API](#4-neo4j-graph-database-rest-api)
   - [Graph Health & Analytics](#graph-health--analytics)
   - [Interactive Graph Traversal (Cytoscape Format)](#interactive-graph-traversal-cytoscape-format)
   - [Graph Entity Traversal & Node CRUD](#graph-entity-traversal--node-crud)
5. [Standard HTTP Status Codes & Error Responses](#5-standard-http-status-codes--error-responses)

---

## 1. Authentication & Security Endpoints

### 1.1 `POST /api/auth/login`
Authenticates user credentials, initializes an encrypted session cookie, and returns a CSRF token for mutating requests.

- **Access:** Public
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "email": "admin@scholarship.demo",
  "password": "Demo@12345",
  "remember": true
}
```
- **Response Headers:** `Set-Cookie: session=<session_token>; HttpOnly; Path=/; SameSite=Lax`
- **Response `200 OK`:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "email": "admin@scholarship.demo",
    "role": "admin",
    "name": "Demo Administrator"
  },
  "csrf_token": "a8f3b2...c91e"
}
```
- **Response `401 Unauthorized`:**
```json
{
  "error": "Invalid email or password"
}
```

---

### 1.2 `GET /api/auth/csrf`
Retrieves or regenerates the active CSRF token for the authenticated session.

- **Access:** Authenticated Session
- **Response `200 OK`:**
```json
{
  "csrf_token": "a8f3b2...c91e"
}
```

---

### 1.3 `GET /api/auth/me`
Verifies the current session state and returns active user metadata.

- **Access:** Authenticated Session
- **Response `200 OK`:**
```json
{
  "authenticated": true,
  "user": {
    "email": "admin@scholarship.demo",
    "role": "admin",
    "name": "Demo Administrator"
  }
}
```
- **Response `401 Unauthorized`:**
```json
{
  "authenticated": false,
  "error": "Not authenticated"
}
```

---

### 1.4 `POST /api/auth/logout`
Destroys the server-side session and invalidates the client cookie.

- **Access:** Authenticated Session
- **Response Headers:** `Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/`
- **Response `200 OK`:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 2. System Health & Diagnostics

### 2.1 `GET /api/health`
Performs live connectivity checks against the Flask application layer, Oracle Database 23ai, and Neo4j Graph Database.

- **Access:** Public / Diagnostic
- **Query Parameters:** None
- **Response `200 OK` (All services healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2026-10-24T00:15:00.000000",
  "active_engine": "oracle",
  "services": {
    "flask": {
      "status": "running",
      "version": "3.1.0"
    },
    "oracle": {
      "status": "connected",
      "host": "localhost",
      "port": 1521,
      "service_name": "FREEPDB1"
    },
    "neo4j": {
      "status": "connected",
      "bolt_url": "bolt://localhost:7687",
      "node_count": 94,
      "relationship_count": 118
    }
  }
}
```

---

## 3. Oracle Core Business REST API

All routes below support dual-mode query parameter `?engine=oracle` (default) or `?engine=neo4j` to compare execution across database engines.

### Dashboard Metrics

#### `GET /api/dashboard`
Computes financial and enrollment metrics across relational tables.

- **Access:** Authenticated
- **Response `200 OK`:**
```json
{
  "engine": "oracle",
  "total_students": 15,
  "total_scholarships_sanctioned": 8,
  "total_scholarship_amount": 420000.00,
  "total_fees_invoiced": 1250000.00,
  "total_fees_collected": 980000.00,
  "outstanding_balance": 270000.00,
  "pending_applications": 3
}
```

---

### Students & Profiles

#### `GET /api/students`
Lists students with academic program details.

- **Query Parameters:**
  - `search` (string, optional): Search by student name or roll number.
  - `program` (string, optional): Filter by program ID (e.g., `P001`).
- **Response `200 OK`:**
```json
[
  {
    "StudentID": "S001",
    "StudentName": "Rahul Sharma",
    "Phone": "9876543210",
    "ProgramID": "P001",
    "ProgramName": "B.Tech Computer Science and Engineering",
    "DegreeLevel": "Undergraduate",
    "DeptName": "Computer Science & Engineering"
  }
]
```

#### `GET /api/students/<student_id>`
Retrieves full student dossier (profile, guardian, scholarships, fees, and payments).

- **URL Parameter:** `student_id` (e.g., `S001`)
- **Response `200 OK`:**
```json
{
  "student": {
    "StudentID": "S001",
    "StudentName": "Rahul Sharma",
    "Phone": "9876543210",
    "HouseNo": "12-A",
    "Street": "MG Road",
    "City": "Bengaluru",
    "PIN": "560001",
    "ProgramID": "P001",
    "ProgramName": "B.Tech Computer Science and Engineering"
  },
  "profile": {
    "BloodGroup": "O+",
    "Nationality": "Indian",
    "DateOfBirth": "2003-05-15",
    "Email": "rahul.sharma@example.edu"
  },
  "guardians": [
    {
      "GuardianID": "G001",
      "GuardianName": "Sunil Sharma",
      "Relation": "Father",
      "PhoneNo": "9876500001",
      "EmailID": "sunil.sharma@example.com"
    }
  ],
  "scholarships": [
    {
      "ScholarshipID": "SCH001",
      "ScholarshipType": "Merit Scholarship",
      "Amount": 50000.00,
      "ApplicationStatus": "Approved"
    }
  ],
  "fees": [
    {
      "FeeID": "F001",
      "FeeAmount": 75000.00,
      "DueDate": "2026-08-31",
      "TotalPaid": 75000.00,
      "Outstanding": 0.00
    }
  ]
}
```

#### `POST /api/students`
Registers a new student record.

- **Request Headers:** `Content-Type: application/json`, `X-CSRFToken: <token>`
- **Request Body:**
```json
{
  "StudentID": "S020",
  "StudentName": "Ananya Roy",
  "Phone": "9812345678",
  "ProgramID": "P001",
  "HouseNo": "44",
  "Street": "Park Street",
  "City": "Kolkata",
  "PIN": "700016"
}
```
- **Response `201 Created`:**
```json
{
  "success": true,
  "message": "Student S020 registered successfully",
  "student_id": "S020"
}
```

---

### Scholarship Applications & Awards

#### `GET /api/applications`
Lists scholarship applications. Supports filter `?status=Pending`.

- **Response `200 OK`:**
```json
[
  {
    "ApplicationID": "A001",
    "StudentID": "S001",
    "StudentName": "Rahul Sharma",
    "ApplicationDate": "2026-01-10",
    "ApplicationStatus": "Approved",
    "ScholarshipID": "SCH001",
    "ScholarshipType": "Merit Scholarship",
    "ScholarshipAmount": 50000.00
  }
]
```

#### `POST /api/applications`
Submits a new scholarship application.

- **Request Body:**
```json
{
  "ApplicationID": "A016",
  "StudentID": "S002",
  "ApplicationDate": "2026-10-24"
}
```
- **Response `201 Created`:**
```json
{
  "success": true,
  "message": "Application A016 submitted successfully"
}
```

#### `PUT /api/applications/<application_id>/status`
Evaluates application and updates status to `Approved` or `Rejected`.

- **Request Body:**
```json
{
  "status": "Approved"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "message": "Application A016 status updated to Approved"
}
```

#### `POST /api/scholarships`
Sanctions a new scholarship grant for an approved application.

- **Request Body:**
```json
{
  "ScholarshipID": "SCH009",
  "ApplicationID": "A016",
  "ScholarshipType": "Academic Excellence Grant",
  "Amount": 60000.00
}
```
- **Response `201 Created`:**
```json
{
  "success": true,
  "message": "Scholarship SCH009 sanctioned successfully"
}
```

---

### Disbursements & Bank Accounts

#### `GET /api/disbursements`
Lists all released grant disbursements with student and bank details.

- **Response `200 OK`:**
```json
[
  {
    "DisbursementID": "D001",
    "StudentID": "S001",
    "StudentName": "Rahul Sharma",
    "ScholarshipID": "SCH001",
    "ScholarshipType": "Merit Scholarship",
    "DisbursedAmount": 50000.00,
    "DisbursementDate": "2026-02-01",
    "DisbursementMode": "Bank Transfer",
    "AccountNo": "ACC1001",
    "BankName": "State Bank of India",
    "IFSC": "SBIN0001234"
  }
]
```

#### `POST /api/disbursements`
Releases a disbursement installment for an approved scholarship.

- **Request Body:**
```json
{
  "DisbursementID": "D010",
  "ScholarshipID": "SCH001",
  "AccountNo": "ACC1001",
  "DisbursementDate": "2026-10-24",
  "Amount": 25000.00,
  "DisbursementMode": "Bank Transfer"
}
```
- **Response `201 Created`:**
```json
{
  "success": true,
  "message": "Disbursement D010 processed successfully"
}
```

---

### Fees, Payments & Offset Validation

#### `GET /api/fees`
Lists fee records, totals paid, and outstanding balances.

- **Response `200 OK`:**
```json
[
  {
    "FeeID": "F001",
    "StudentID": "S001",
    "StudentName": "Rahul Sharma",
    "FeeAmount": 75000.00,
    "DueDate": "2026-08-31",
    "TotalPaid": 75000.00,
    "OutstandingAmount": 0.00
  }
]
```

#### `POST /api/payments`
Records a fee payment. Enforces the PL/SQL database trigger `TRG_CHECK_FEE_PAYMENT`.

- **Request Body:**
```json
{
  "PaymentID": "PAY015",
  "FeeID": "F002",
  "MethodID": "M001",
  "ScholarshipID": null,
  "PaymentDate": "2026-10-24",
  "AmountPaid": 20000.00,
  "TransactionID": "TXN99283100"
}
```
- **Response `201 Created` (Success):**
```json
{
  "success": true,
  "message": "Payment PAY015 recorded successfully"
}
```
- **Response `400 Bad Request` (Trigger Violation — Payment Exceeds Fee):**
```json
{
  "error": "Payment exceeds the total fee amount (ORA-20001 triggered by TRG_CHECK_FEE_PAYMENT)"
}
```

---

## 4. Neo4j Graph Database REST API

Prefix: `/api/neo4j`

### Graph Health & Analytics

#### `GET /api/neo4j/health`
Checks graph connectivity and structural cardinality.

- **Response `200 OK`:**
```json
{
  "status": "connected",
  "node_count": 94,
  "relationship_count": 118,
  "labels": ["Department", "Program", "Student", "StudentProfile", "Guardian", "Application", "Scholarship", "BankAccount", "Disbursement", "Fee", "PaymentMethod", "Payment"]
}
```

#### `GET /api/neo4j/dashboard`
Calculates graph density, degree metrics, and cross-entity summaries.

- **Response `200 OK`:**
```json
{
  "total_nodes": 94,
  "total_relationships": 118,
  "node_counts": {
    "Student": 15,
    "Program": 4,
    "Department": 3,
    "Application": 15,
    "Scholarship": 8,
    "Disbursement": 8,
    "Fee": 15,
    "Payment": 12,
    "BankAccount": 8,
    "Guardian": 15,
    "StudentProfile": 15,
    "PaymentMethod": 4
  }
}
```

---

### Interactive Graph Traversal (Cytoscape Format)

#### `GET /api/neo4j/graph`
Extracts graph subsets in Cytoscape.js format for visual exploration.

- **Query Parameters:**
  - `preset`: `student_journey` | `all` | `scholarships` | `fees`
  - `student_id` (string, optional): Focal student ID (e.g., `S001`)
  - `limit` (integer, default: `50`): Maximum relationships to traverse
- **Example Request:** `GET /api/neo4j/graph?preset=student_journey&student_id=S001`
- **Response `200 OK`:**
```json
{
  "elements": {
    "nodes": [
      {
        "data": {
          "id": "Student_S001",
          "label": "Student",
          "name": "Rahul Sharma",
          "studentId": "S001"
        }
      },
      {
        "data": {
          "id": "Program_P001",
          "label": "Program",
          "name": "B.Tech CSE",
          "programId": "P001"
        }
      },
      {
        "data": {
          "id": "Application_A001",
          "label": "Application",
          "applicationId": "A001",
          "status": "Approved"
        }
      },
      {
        "data": {
          "id": "Scholarship_SCH001",
          "label": "Scholarship",
          "scholarshipId": "SCH001",
          "amount": 50000.00
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "e_Program_P001_HAS_STUDENT_Student_S001",
          "source": "Program_P001",
          "target": "Student_S001",
          "label": "HAS_STUDENT"
        }
      },
      {
        "data": {
          "id": "e_Student_S001_SUBMITTED_Application_A001",
          "source": "Student_S001",
          "target": "Application_A001",
          "label": "SUBMITTED"
        }
      },
      {
        "data": {
          "id": "e_Application_A001_AWARDS_Scholarship_SCH001",
          "source": "Application_A001",
          "target": "Scholarship_SCH001",
          "label": "AWARDS"
        }
      }
    ]
  }
}
```

---

### Graph Entity Traversal & Node CRUD

| Endpoint | Method | Description | Cypher Traversal |
|---|---|---|---|
| `/api/neo4j/students/<student_id>` | `GET` | Traverse 1-hop and 2-hop neighborhood of a student node | `MATCH (s:Student {studentId: $id})-[r]-(n) RETURN s, r, n` |
| `/api/neo4j/students/<student_id>/profile` | `GET` | Retrieve student profile via graph edge | `MATCH (s:Student {studentId: $id})-[:HAS_PROFILE]->(p) RETURN p` |
| `/api/neo4j/students/<student_id>/guardians` | `GET` | Retrieve guardian nodes linked to student | `MATCH (s:Student {studentId: $id})-[:HAS_GUARDIAN]->(g) RETURN g` |
| `/api/neo4j/students/<student_id>/applications` | `GET` | Traverse all applications submitted by student | `MATCH (s:Student {studentId: $id})-[:SUBMITTED]->(a) RETURN a` |
| `/api/neo4j/students/<student_id>/scholarships` | `GET` | Traverse awarded scholarships | `MATCH (s:Student {studentId: $id})-[:SUBMITTED]->(a)-[:AWARDS]->(sch) RETURN sch` |
| `/api/neo4j/students/<student_id>/fees` | `GET` | Retrieve fee liability nodes | `MATCH (s:Student {studentId: $id})-[:HAS_FEE]->(f) RETURN f` |
| `/api/neo4j/students/<student_id>/payments` | `GET` | Retrieve payments settled for student fees | `MATCH (s:Student {studentId: $id})-[:HAS_FEE]->(f)-[:HAS_PAYMENT]->(p) RETURN p` |
| `/api/neo4j/programs/<program_id>/students` | `GET` | List all students enrolled in a specific program | `MATCH (p:Program {programId: $id})-[:HAS_STUDENT]->(s) RETURN s` |
| `/api/neo4j/nodes/<label>` | `GET` | Generic node scan by label | `MATCH (n:<label>) RETURN n LIMIT 100` |
| `/api/neo4j/nodes/<label>` | `POST` | Generic node insertion with uniqueness constraint | `MERGE (n:<label> {<uniqueKey>: $id}) SET n += $props RETURN n` |

---

## 5. Standard HTTP Status Codes & Error Responses

| Code | Name | Description |
|---|---|---|
| `200 OK` | Successful Request | Standard response for successful GET, PUT, or DELETE operations. |
| `201 Created` | Resource Created | Standard response for successful POST creation requests. |
| `400 Bad Request` | Validation Error | Payload is missing required fields, or violates a business rule (e.g., fee overpayment). |
| `401 Unauthorized` | Authentication Required | Client is not authenticated via session cookie or credentials are invalid. |
| `403 Forbidden` | CSRF or Permission Failure | Mutating request lacks a valid `X-CSRFToken` header. |
| `404 Not Found` | Entity Missing | Requested student, application, scholarship, or fee does not exist. |
| `409 Conflict` | Unique Key Collision | Duplicate primary key or unique constraint violation. |
| `500 Server Error` | Database Failure | Unhandled exception or database connection timeout. |

Standard JSON Error Schema:
```json
{
  "error": "Human-readable explanation of the error",
  "code": "ERR_SPECIFIC_CODE",
  "details": null
}
```
