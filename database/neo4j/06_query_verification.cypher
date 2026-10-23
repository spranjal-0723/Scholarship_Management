/*
 DA-3 Member 3: additional business and financial verification queries.
 Uses the canonical schema from docs/da3_graph_schema.md.
 Run each semicolon-terminated query separately in Neo4j Browser.
 These queries read data only; they do not modify the graph.
*/

// QUERY 1: Applications that are currently Pending
MATCH (student:Student)-[:SUBMITTED]->(application:Application)
WHERE application.applicationStatus = 'Pending'
RETURN application.applicationId AS applicationId,
       student.studentId AS studentId,
       student.studentName AS studentName,
       application.applicationDate AS applicationDate,
       application.applicationStatus AS status
ORDER BY applicationDate, applicationId;

// QUERY 2: Approved applications with no linked scholarship
MATCH (application:Application)
WHERE application.applicationStatus = 'Approved'
OPTIONAL MATCH (application)-[:AWARDS]->(scholarship:Scholarship)
WITH application, scholarship
WHERE scholarship IS NULL
OPTIONAL MATCH (student:Student)-[:SUBMITTED]->(application)
RETURN application.applicationId AS applicationId,
       student.studentId AS studentId,
       student.studentName AS studentName,
       application.applicationStatus AS status
ORDER BY applicationId;

// QUERY 3: Scholarships with no linked disbursement
MATCH (scholarship:Scholarship)
OPTIONAL MATCH (scholarship)-[:HAS_DISBURSEMENT]->(disbursement:Disbursement)
WITH scholarship, collect(disbursement) AS disbursements
WHERE size(disbursements) = 0
RETURN scholarship.scholarshipId AS scholarshipId,
       scholarship.scholarshipType AS scholarshipType,
       scholarship.amount AS scholarshipAmount
ORDER BY scholarshipId;

// QUERY 4: Outstanding fees by student (aggregate payments per fee first)
MATCH (student:Student)-[:HAS_FEE]->(fee:Fee)
CALL {
    WITH fee
    OPTIONAL MATCH (fee)-[:HAS_PAYMENT]->(payment:Payment)
    RETURN coalesce(sum(payment.amountPaid), 0) AS totalPaid
}
WITH student, fee, totalPaid, fee.feeAmount - totalPaid AS outstandingAmount
WHERE outstandingAmount > 0
RETURN student.studentId AS studentId,
       student.studentName AS studentName,
       fee.feeId AS feeId,
       fee.feeAmount AS feeAmount,
       totalPaid AS totalPaid,
       outstandingAmount AS outstandingAmount,
       fee.dueDate AS dueDate
ORDER BY outstandingAmount DESC, studentId;

// QUERY 5: Scholarship amounts grouped by scholarship type
MATCH (scholarship:Scholarship)
RETURN scholarship.scholarshipType AS scholarshipType,
       count(scholarship) AS scholarshipCount,
       sum(scholarship.amount) AS totalScholarshipAmount
ORDER BY scholarshipType;

// QUERY 6: Number of applications by status
MATCH (application:Application)
RETURN application.applicationStatus AS applicationStatus,
       count(*) AS applicationCount
ORDER BY applicationStatus;

// QUERY 7: Financial baseline totals (independent subqueries avoid cross-product multiplication)
CALL {
    MATCH (fee:Fee)
    RETURN coalesce(sum(fee.feeAmount), 0) AS totalFees
}
CALL {
    MATCH (payment:Payment)
    RETURN coalesce(sum(payment.amountPaid), 0) AS totalPaid
}
RETURN totalFees,
       totalPaid,
       totalFees - totalPaid AS totalOutstanding;

// QUERY 8: Students with multiple applications or multiple payments
MATCH (student:Student)
CALL {
    WITH student
    OPTIONAL MATCH (student)-[:SUBMITTED]->(application:Application)
    RETURN count(application) AS applicationCount
}
CALL {
    WITH student
    OPTIONAL MATCH (student)-[:HAS_FEE]->(:Fee)-[:HAS_PAYMENT]->(payment:Payment)
    RETURN count(payment) AS paymentCount
}
WITH student, applicationCount, paymentCount
WHERE applicationCount > 1 OR paymentCount > 1
RETURN student.studentId AS studentId,
       student.studentName AS studentName,
       applicationCount,
       paymentCount
ORDER BY studentId;

// QUERY 9: Total disbursed amount, calculated directly from Disbursement nodes
MATCH (disbursement:Disbursement)
RETURN count(disbursement) AS disbursementCount,
       coalesce(sum(disbursement.amount), 0) AS totalDisbursed;
