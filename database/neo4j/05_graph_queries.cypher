/*
 DA-3 Member 3: Advanced Cypher query collection

 Uses the canonical labels, properties, and relationships documented in
 docs/da3_graph_schema.md. This file does not create or modify schema.

 Run each query separately in Neo4j Browser.
*/

// ============================================================
// QUERY 1: Student scholarship journey
// Student -> Application -> Scholarship -> Disbursement -> BankAccount
// OPTIONAL MATCH keeps students/applications visible when later links
// do not exist yet. One row represents one available journey/path.
// ============================================================
MATCH (student:Student)
OPTIONAL MATCH (student)-[:SUBMITTED]->(application:Application)
OPTIONAL MATCH (application)-[:AWARDS]->(scholarship:Scholarship)
OPTIONAL MATCH (scholarship)-[:HAS_DISBURSEMENT]->(disbursement:Disbursement)
OPTIONAL MATCH (disbursement)-[:TO_ACCOUNT]->(account:BankAccount)
RETURN
    student.studentId AS studentId,
    student.studentName AS studentName,
    application.applicationId AS applicationId,
    application.applicationStatus AS applicationStatus,
    scholarship.scholarshipId AS scholarshipId,
    scholarship.scholarshipType AS scholarshipType,
    scholarship.amount AS scholarshipAmount,
    disbursement.disbursementId AS disbursementId,
    disbursement.amount AS disbursedAmount,
    disbursement.disbursementMode AS disbursementMode,
    account.accountNo AS accountNo,
    account.bankName AS bankName
ORDER BY studentId, applicationId, scholarshipId, disbursementId;


// ============================================================
// QUERY 2: Department-wise scholarship exploration
// Department -> Program -> Student -> Application -> Scholarship
// This describes linked records; it does NOT decide eligibility.
// OPTIONAL MATCH preserves students even if they have no application
// or no scholarship linked to that application.
// ============================================================
MATCH (department:Department)-[:HAS_PROGRAM]->(program:Program)-[:HAS_STUDENT]->(student:Student)
OPTIONAL MATCH (student)-[:SUBMITTED]->(application:Application)
OPTIONAL MATCH (application)-[:AWARDS]->(scholarship:Scholarship)
RETURN
    department.deptId AS deptId,
    department.deptName AS department,
    program.programId AS programId,
    program.programName AS program,
    student.studentId AS studentId,
    student.studentName AS studentName,
    application.applicationId AS applicationId,
    application.applicationStatus AS applicationStatus,
    scholarship.scholarshipId AS scholarshipId,
    scholarship.scholarshipType AS scholarshipType,
    scholarship.amount AS scholarshipAmount
ORDER BY department, program, studentName, applicationId;


// ============================================================
// QUERY 3: Financial traceability per student fee
// Student -> Fee -> Payment -> PaymentMethod, with optional Scholarship
// A separate subquery calculates total paid per fee, so adding optional
// method/scholarship details cannot multiply the amount-paid total.
// Outstanding is calculated from fee amount minus actual linked payments.
// ============================================================
MATCH (student:Student)-[:HAS_FEE]->(fee:Fee)
CALL {
    WITH fee
    OPTIONAL MATCH (fee)-[:HAS_PAYMENT]->(payment:Payment)
    RETURN coalesce(sum(payment.amountPaid), 0) AS totalPaid
}
CALL {
    WITH fee
    OPTIONAL MATCH (fee)-[:HAS_PAYMENT]->(payment:Payment)
    OPTIONAL MATCH (payment)-[:PAID_VIA]->(method:PaymentMethod)
    OPTIONAL MATCH (payment)-[:USES_SCHOLARSHIP]->(scholarship:Scholarship)
    RETURN collect(DISTINCT CASE
        WHEN payment IS NULL THEN null
        ELSE {
            paymentId: payment.paymentId,
            paymentDate: payment.paymentDate,
            amountPaid: payment.amountPaid,
            transactionId: payment.transactionId,
            methodId: method.methodId,
            methodName: method.methodName,
            scholarshipId: scholarship.scholarshipId,
            scholarshipType: scholarship.scholarshipType
        }
    END) AS paymentDetails
}
RETURN
    student.studentId AS studentId,
    student.studentName AS studentName,
    fee.feeId AS feeId,
    fee.feeAmount AS feeAmount,
    fee.dueDate AS dueDate,
    totalPaid AS totalPaid,
    fee.feeAmount - totalPaid AS outstandingAmount,
    paymentDetails AS payments
ORDER BY studentId, feeId;
