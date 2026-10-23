
/*
 DA-3: Import the existing DA-2 sample records into Neo4j.
 MERGE makes this script safe to rerun for the same canonical IDs.
 Source: database/03_sample_data.sql
*/

 // 1. DEPARTMENT
UNWIND [
  {deptId:'D01', deptName:'Computer Science'},
  {deptId:'D02', deptName:'Electronics'},
  {deptId:'D03', deptName:'Mechanical Engineering'}
] AS row
MERGE (n:Department {deptId:row.deptId})
SET n.deptName = row.deptName;

// 2. PROGRAM
UNWIND [
  {programId:'P01', programName:'Computer Science and Engineering', degreeLevel:'BTech', deptId:'D01'},
  {programId:'P02', programName:'Electronics and Communication Engineering', degreeLevel:'BTech', deptId:'D02'},
  {programId:'P03', programName:'Mechanical Engineering', degreeLevel:'BTech', deptId:'D03'}
] AS row
MERGE (n:Program {programId:row.programId})
SET n.programName = row.programName,
    n.degreeLevel = row.degreeLevel,
    n.deptId = row.deptId;

// 3. STUDENT
UNWIND [
  {studentId:'S001', studentName:'Aarav Sharma', phone:'9876543210', houseNo:'12A', street:'MG Road', city:'Chennai', pin:'600001', programId:'P01'},
  {studentId:'S002', studentName:'Priya Nair', phone:'9876543211', houseNo:'24B', street:'Anna Nagar', city:'Chennai', pin:'600040', programId:'P02'},
  {studentId:'S003', studentName:'Rahul Verma', phone:'9876543212', houseNo:'15C', street:'Gandhi Road', city:'Chennai', pin:'600020', programId:'P03'},
  {studentId:'S004', studentName:'Ananya Singh', phone:'9876543213', houseNo:'8D', street:'OMR Road', city:'Chennai', pin:'600096', programId:'P01'},
  {studentId:'S005', studentName:'Karan Patel', phone:'9876543214', houseNo:'17E', street:'Velachery Road', city:'Chennai', pin:'600042', programId:'P02'}
] AS row
MERGE (n:Student {studentId:row.studentId})
SET n.studentName = row.studentName,
    n.phone = row.phone,
    n.houseNo = row.houseNo,
    n.street = row.street,
    n.city = row.city,
    n.pin = row.pin,
    n.programId = row.programId;

// 4. STUDENT_PROFILE
UNWIND [
  {studentId:'S001', bloodGroup:'O+', nationality:'Indian', dateOfBirth:date('2006-05-14'), email:'aarav@example.com'},
  {studentId:'S002', bloodGroup:'A+', nationality:'Indian', dateOfBirth:date('2005-11-22'), email:'priya@example.com'},
  {studentId:'S003', bloodGroup:'B+', nationality:'Indian', dateOfBirth:date('2006-02-18'), email:'rahul@example.com'},
  {studentId:'S004', bloodGroup:'AB+', nationality:'Indian', dateOfBirth:date('2006-08-30'), email:'ananya@example.com'},
  {studentId:'S005', bloodGroup:'O-', nationality:'Indian', dateOfBirth:date('2005-12-10'), email:'karan@example.com'}
] AS row
MERGE (n:StudentProfile {studentId:row.studentId})
SET n.bloodGroup = row.bloodGroup,
    n.nationality = row.nationality,
    n.dateOfBirth = row.dateOfBirth,
    n.email = row.email;

// 5. GUARDIAN
UNWIND [
  {guardianId:'G001', studentId:'S001', guardianName:'Ramesh Sharma', relation:'Father', phoneNo:'9876500010', emailId:'ramesh@example.com'},
  {guardianId:'G002', studentId:'S002', guardianName:'Suresh Nair', relation:'Father', phoneNo:'9876500011', emailId:'suresh@example.com'},
  {guardianId:'G003', studentId:'S003', guardianName:'Mahesh Verma', relation:'Father', phoneNo:'9876500012', emailId:'mahesh@example.com'},
  {guardianId:'G004', studentId:'S004', guardianName:'Rajesh Singh', relation:'Father', phoneNo:'9876500013', emailId:'rajesh@example.com'},
  {guardianId:'G005', studentId:'S005', guardianName:'Dinesh Patel', relation:'Father', phoneNo:'9876500014', emailId:'dinesh@example.com'}
] AS row
MERGE (n:Guardian {guardianId:row.guardianId})
SET n.guardianName = row.guardianName,
    n.relation = row.relation,
    n.phoneNo = row.phoneNo,
    n.emailId = row.emailId,
    n.studentId = row.studentId;

// 6. SCHOLARSHIP_APPLICATION
UNWIND [
  {applicationId:'APP001', studentId:'S001', applicationDate:date('2026-01-10'), applicationStatus:'Approved'},
  {applicationId:'APP002', studentId:'S002', applicationDate:date('2026-01-12'), applicationStatus:'Pending'},
  {applicationId:'APP003', studentId:'S003', applicationDate:date('2026-01-15'), applicationStatus:'Approved'},
  {applicationId:'APP004', studentId:'S004', applicationDate:date('2026-01-18'), applicationStatus:'Rejected'},
  {applicationId:'APP005', studentId:'S005', applicationDate:date('2026-01-20'), applicationStatus:'Approved'}
] AS row
MERGE (n:Application {applicationId:row.applicationId})
SET n.studentId = row.studentId,
    n.applicationDate = row.applicationDate,
    n.applicationStatus = row.applicationStatus;

// 7. SCHOLARSHIP
UNWIND [
  {scholarshipId:'SCH001', applicationId:'APP001', scholarshipType:'Merit Scholarship', amount:50000},
  {scholarshipId:'SCH002', applicationId:'APP002', scholarshipType:'Need Based Scholarship', amount:30000},
  {scholarshipId:'SCH003', applicationId:'APP003', scholarshipType:'Sports Scholarship', amount:40000},
  {scholarshipId:'SCH004', applicationId:'APP004', scholarshipType:'Merit Scholarship', amount:25000},
  {scholarshipId:'SCH005', applicationId:'APP005', scholarshipType:'Need Based Scholarship', amount:35000}
] AS row
MERGE (n:Scholarship {scholarshipId:row.scholarshipId})
SET n.applicationId = row.applicationId,
    n.scholarshipType = row.scholarshipType,
    n.amount = row.amount;

// 8. BANK_ACCOUNT
UNWIND [
  {accountNo:'AC001', bankName:'State Bank of India', ifsc:'SBIN0001234', accountType:'Savings'},
  {accountNo:'AC002', bankName:'HDFC Bank', ifsc:'HDFC0001234', accountType:'Savings'},
  {accountNo:'AC003', bankName:'ICICI Bank', ifsc:'ICIC0001234', accountType:'Savings'},
  {accountNo:'AC004', bankName:'Axis Bank', ifsc:'UTIB0001234', accountType:'Savings'},
  {accountNo:'AC005', bankName:'Punjab National Bank', ifsc:'PUNB0001234', accountType:'Savings'}
] AS row
MERGE (n:BankAccount {accountNo:row.accountNo})
SET n.bankName = row.bankName,
    n.ifsc = row.ifsc,
    n.accountType = row.accountType;

// 9. DISBURSEMENT
UNWIND [
  {disbursementId:'DIS001', scholarshipId:'SCH001', accountNo:'AC001', disbursementDate:date('2026-02-10'), amount:50000, disbursementMode:'Bank Transfer'},
  {disbursementId:'DIS002', scholarshipId:'SCH002', accountNo:'AC002', disbursementDate:date('2026-02-02'), amount:30000, disbursementMode:'Direct Transfer'},
  {disbursementId:'DIS003', scholarshipId:'SCH003', accountNo:'AC003', disbursementDate:date('2026-02-15'), amount:40000, disbursementMode:'Bank Transfer'},
  {disbursementId:'DIS004', scholarshipId:'SCH005', accountNo:'AC005', disbursementDate:date('2026-02-20'), amount:35000, disbursementMode:'Bank Transfer'}
] AS row
MERGE (n:Disbursement {disbursementId:row.disbursementId})
SET n.scholarshipId = row.scholarshipId,
    n.accountNo = row.accountNo,
    n.disbursementDate = row.disbursementDate,
    n.amount = row.amount,
    n.disbursementMode = row.disbursementMode;

// 10. STUDENT_FEE
UNWIND [
  {feeId:'F001', studentId:'S001', feeAmount:75000, dueDate:date('2026-03-01')},
  {feeId:'F002', studentId:'S002', feeAmount:80000, dueDate:date('2026-03-01')},
  {feeId:'F003', studentId:'S003', feeAmount:70000, dueDate:date('2026-03-01')},
  {feeId:'F004', studentId:'S004', feeAmount:75000, dueDate:date('2026-03-01')},
  {feeId:'F005', studentId:'S005', feeAmount:80000, dueDate:date('2026-03-01')}
] AS row
MERGE (n:Fee {feeId:row.feeId})
SET n.studentId = row.studentId,
    n.feeAmount = row.feeAmount,
    n.dueDate = row.dueDate;

// 11. PAYMENT_METHOD
UNWIND [
  {methodId:'M01', methodName:'UPI'},
  {methodId:'M02', methodName:'Net Banking'},
  {methodId:'M03', methodName:'Credit Card'},
  {methodId:'M04', methodName:'Debit Card'}
] AS row
MERGE (n:PaymentMethod {methodId:row.methodId})
SET n.methodName = row.methodName;

// 12. FEE_PAYMENT
UNWIND [
  {paymentId:'PAY001', feeId:'F001', scholarshipId:'SCH001', methodId:'M01', paymentDate:date('2026-02-25'), amountPaid:25000, transactionId:'TXN1001'},
  {paymentId:'PAY002', feeId:'F002', scholarshipId:'SCH002', methodId:'M02', paymentDate:date('2026-02-26'), amountPaid:20000, transactionId:'TXN1002'},
  {paymentId:'PAY003', feeId:'F003', scholarshipId:'SCH003', methodId:'M03', paymentDate:date('2026-02-27'), amountPaid:30000, transactionId:'TXN1003'},
  {paymentId:'PAY004', feeId:'F005', scholarshipId:'SCH005', methodId:'M04', paymentDate:date('2026-02-28'), amountPaid:15000, transactionId:'TXN1004'},
  {paymentId:'PAY005', feeId:'F001', scholarshipId:null, methodId:'M01', paymentDate:date('2026-03-02'), amountPaid:10000, transactionId:'TXN1005'}
] AS row
MERGE (n:Payment {paymentId:row.paymentId})
SET n.feeId = row.feeId,
    n.scholarshipId = row.scholarshipId,
    n.methodId = row.methodId,
    n.paymentDate = row.paymentDate,
    n.amountPaid = row.amountPaid,
    n.transactionId = row.transactionId;
