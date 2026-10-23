
/*
 DA-3: Create graph relationships from existing foreign keys.
 Run after 01_constraints.cypher and 02_import_data.cypher.
*/

 // Department -> Program
MATCH (d:Department), (p:Program)
WHERE p.deptId = d.deptId
MERGE (d)-[:HAS_PROGRAM]->(p);

// Program -> Student
MATCH (p:Program), (s:Student)
WHERE s.programId = p.programId
MERGE (p)-[:HAS_STUDENT]->(s);

// Student -> StudentProfile
MATCH (s:Student), (p:StudentProfile)
WHERE p.studentId = s.studentId
MERGE (s)-[:HAS_PROFILE]->(p);

// Student -> Guardian
MATCH (s:Student), (g:Guardian)
WHERE g.studentId = s.studentId
MERGE (s)-[:HAS_GUARDIAN]->(g);

// Student -> Application
MATCH (s:Student), (a:Application)
WHERE a.studentId = s.studentId
MERGE (s)-[:SUBMITTED]->(a);

// Application -> Scholarship
MATCH (a:Application), (sch:Scholarship)
WHERE sch.applicationId = a.applicationId
MERGE (a)-[:AWARDS]->(sch);

// Scholarship -> Disbursement
MATCH (sch:Scholarship), (d:Disbursement)
WHERE d.scholarshipId = sch.scholarshipId
MERGE (sch)-[:HAS_DISBURSEMENT]->(d);

// Disbursement -> BankAccount
MATCH (d:Disbursement), (b:BankAccount)
WHERE d.accountNo = b.accountNo
MERGE (d)-[:TO_ACCOUNT]->(b);

// Student -> Fee
MATCH (s:Student), (f:Fee)
WHERE f.studentId = s.studentId
MERGE (s)-[:HAS_FEE]->(f);

// Fee -> Payment
MATCH (f:Fee), (p:Payment)
WHERE p.feeId = f.feeId
MERGE (f)-[:HAS_PAYMENT]->(p);

// Payment -> PaymentMethod
MATCH (p:Payment), (m:PaymentMethod)
WHERE p.methodId = m.methodId
MERGE (p)-[:PAID_VIA]->(m);

// Payment -> Scholarship (optional foreign key)
MATCH (p:Payment), (sch:Scholarship)
WHERE p.scholarshipId IS NOT NULL
  AND p.scholarshipId = sch.scholarshipId
MERGE (p)-[:USES_SCHOLARSHIP]->(sch);
