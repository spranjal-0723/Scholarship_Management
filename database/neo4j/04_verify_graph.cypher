
/*
 DA-3: Graph verification
 Run after importing nodes and creating relationships.
*/

/* 1. Node counts by label */
MATCH (n)
UNWIND labels(n) AS label
RETURN label, count(*) AS nodeCount
ORDER BY label;

/* 2. Expected node counts for all 12 labels */
CALL {
    MATCH (n:Department) RETURN 'Department' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Program) RETURN 'Program' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Student) RETURN 'Student' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:StudentProfile) RETURN 'StudentProfile' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Guardian) RETURN 'Guardian' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Application) RETURN 'Application' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Scholarship) RETURN 'Scholarship' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:BankAccount) RETURN 'BankAccount' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Disbursement) RETURN 'Disbursement' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Fee) RETURN 'Fee' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:PaymentMethod) RETURN 'PaymentMethod' AS label, count(n) AS actual
    UNION ALL
    MATCH (n:Payment) RETURN 'Payment' AS label, count(n) AS actual
}
WITH label, actual,
     CASE label
       WHEN 'Department' THEN 3
       WHEN 'Program' THEN 3
       WHEN 'Student' THEN 5
       WHEN 'StudentProfile' THEN 5
       WHEN 'Guardian' THEN 5
       WHEN 'Application' THEN 5
       WHEN 'Scholarship' THEN 5
       WHEN 'BankAccount' THEN 5
       WHEN 'Disbursement' THEN 4
       WHEN 'Fee' THEN 5
       WHEN 'PaymentMethod' THEN 4
       WHEN 'Payment' THEN 5
     END AS expected
RETURN label, expected, actual,
       actual = expected AS countMatches
ORDER BY label;

/* 3. Relationship counts */
MATCH ()-[r]->()
RETURN type(r) AS relationshipType, count(r) AS relationshipCount
ORDER BY relationshipType;

/* 4. Check for payments with missing fee or payment-method relationships */
MATCH (p:Payment)
OPTIONAL MATCH (f:Fee)-[:HAS_PAYMENT]->(p)
OPTIONAL MATCH (p)-[:PAID_VIA]->(m:PaymentMethod)
RETURN p.paymentId AS paymentId,
       f.feeId AS linkedFee,
       m.methodId AS linkedPaymentMethod,
       f IS NOT NULL AND m IS NOT NULL AS linksValid
ORDER BY paymentId;

/* 5. Check for scholarships with missing application links */
MATCH (sch:Scholarship)
OPTIONAL MATCH (a:Application)-[:AWARDS]->(sch)
RETURN sch.scholarshipId AS scholarshipId,
       a.applicationId AS linkedApplication,
       a IS NOT NULL AS linkValid
ORDER BY scholarshipId;

/* 6. Check that every disbursement has a scholarship and account */
MATCH (d:Disbursement)
OPTIONAL MATCH (sch:Scholarship)-[:HAS_DISBURSEMENT]->(d)
OPTIONAL MATCH (d)-[:TO_ACCOUNT]->(b:BankAccount)
RETURN d.disbursementId AS disbursementId,
       sch.scholarshipId AS linkedScholarship,
       b.accountNo AS linkedAccount,
       sch IS NOT NULL AND b IS NOT NULL AS linksValid
ORDER BY disbursementId;

