
# DA-3: Neo4j Graph Database Schema

## 1. Objective

This module represents the Scholarship and Fee Management System
as a property graph in Neo4j. The graph structure is mapped from
the existing DA-2 Oracle relational schema and preserves the
canonical identifiers and source records.

## 2. Node Labels and Canonical Identifiers

| Node label | Canonical identifier | Source Oracle table |
|---|---|---|
| Department | deptId | DEPARTMENT |
| Program | programId | PROGRAM |
| Student | studentId | STUDENT |
| StudentProfile | studentId | STUDENT_PROFILE |
| Guardian | guardianId | GUARDIAN |
| Application | applicationId | SCHOLARSHIP_APPLICATION |
| Scholarship | scholarshipId | SCHOLARSHIP |
| BankAccount | accountNo | BANK_ACCOUNT |
| Disbursement | disbursementId | DISBURSEMENT |
| Fee | feeId | STUDENT_FEE |
| PaymentMethod | methodId | PAYMENT_METHOD |
| Payment | paymentId | FEE_PAYMENT |

Unique constraints are defined for the canonical identifier of
each node label in `database/neo4j/01_constraints.cypher`.

## 3. Relationships

| Source node | Relationship | Target node | Source foreign-key mapping |
|---|---|---|---|
| Department | HAS_PROGRAM | Program | Program.deptId |
| Program | HAS_STUDENT | Student | Student.programId |
| Student | HAS_PROFILE | StudentProfile | StudentProfile.studentId |
| Student | HAS_GUARDIAN | Guardian | Guardian.studentId |
| Student | SUBMITTED | Application | Application.studentId |
| Application | AWARDS | Scholarship | Scholarship.applicationId |
| Scholarship | HAS_DISBURSEMENT | Disbursement | Disbursement.scholarshipId |
| Disbursement | TO_ACCOUNT | BankAccount | Disbursement.accountNo |
| Student | HAS_FEE | Fee | Fee.studentId |
| Fee | HAS_PAYMENT | Payment | Payment.feeId |
| Payment | PAID_VIA | PaymentMethod | Payment.methodId |
| Payment | USES_SCHOLARSHIP | Scholarship | Payment.scholarshipId (optional) |

## 4. Expected Node Counts

| Node label | Expected count |
|---|---:|
| Department | 3 |
| Program | 3 |
| Student | 5 |
| StudentProfile | 5 |
| Guardian | 5 |
| Application | 5 |
| Scholarship | 5 |
| BankAccount | 5 |
| Disbursement | 4 |
| Fee | 5 |
| PaymentMethod | 4 |
| Payment | 5 |
| **Total** | **54** |

These expected counts are derived from the existing DA-2 sample
data. Actual counts must be checked against the Neo4j database
after import.

## 5. Migration and Idempotency

The import script, `database/neo4j/02_import_data.cypher`, uses
`MERGE` with canonical identifiers to avoid creating duplicate
nodes when the script is rerun.

The relationship script, `database/neo4j/03_create_relationships.cypher`,
uses `MERGE` to avoid duplicate relationships of the same type
between the matched nodes.

The source Oracle schema and sample-data files are retained
unchanged.

## 6. Verification

Run the queries in `database/neo4j/04_verify_graph.cypher`
after creating constraints, importing nodes, and creating
relationships.

Verify:
- Node counts against the expected totals.
- Relationship counts and expected connectivity.
- Payment links to fees and payment methods.
- Scholarship links to applications.
- Disbursement links to scholarships and bank accounts.

The scripts are prepared for verification; successful execution
and migration are not claimed until tested in Neo4j.

## 7. Execution Order

1. `01_constraints.cypher`
2. `02_import_data.cypher`
3. `03_create_relationships.cypher`
4. `04_verify_graph.cypher`

Execute each semicolon-separated query individually in Neo4j
Browser. The verification file contains multiple independent
queries.
