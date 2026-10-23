
/*
 DA-3: Neo4j Graph Database
 Unique constraints for the 12 canonical node labels.

 These constraints prevent duplicate nodes when the import
 script is run repeatedly.
*/

CREATE CONSTRAINT department_deptId_unique IF NOT EXISTS
FOR (n:Department)
REQUIRE n.deptId IS UNIQUE;

CREATE CONSTRAINT program_programId_unique IF NOT EXISTS
FOR (n:Program)
REQUIRE n.programId IS UNIQUE;

CREATE CONSTRAINT student_studentId_unique IF NOT EXISTS
FOR (n:Student)
REQUIRE n.studentId IS UNIQUE;

CREATE CONSTRAINT studentProfile_studentId_unique IF NOT EXISTS
FOR (n:StudentProfile)
REQUIRE n.studentId IS UNIQUE;

CREATE CONSTRAINT guardian_guardianId_unique IF NOT EXISTS
FOR (n:Guardian)
REQUIRE n.guardianId IS UNIQUE;

CREATE CONSTRAINT application_applicationId_unique IF NOT EXISTS
FOR (n:Application)
REQUIRE n.applicationId IS UNIQUE;

CREATE CONSTRAINT scholarship_scholarshipId_unique IF NOT EXISTS
FOR (n:Scholarship)
REQUIRE n.scholarshipId IS UNIQUE;

CREATE CONSTRAINT bankAccount_accountNo_unique IF NOT EXISTS
FOR (n:BankAccount)
REQUIRE n.accountNo IS UNIQUE;

CREATE CONSTRAINT disbursement_disbursementId_unique IF NOT EXISTS
FOR (n:Disbursement)
REQUIRE n.disbursementId IS UNIQUE;

CREATE CONSTRAINT fee_feeId_unique IF NOT EXISTS
FOR (n:Fee)
REQUIRE n.feeId IS UNIQUE;

CREATE CONSTRAINT paymentMethod_methodId_unique IF NOT EXISTS
FOR (n:PaymentMethod)
REQUIRE n.methodId IS UNIQUE;

CREATE CONSTRAINT payment_paymentId_unique IF NOT EXISTS
FOR (n:Payment)
REQUIRE n.paymentId IS UNIQUE;
