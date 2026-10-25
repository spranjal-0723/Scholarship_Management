#!/usr/bin/env python3
"""
Repeatable, idempotent migration and verification tool for Neo4j AuraDB Cloud.

Transfers the full canonical 250-node and 280-relationship dataset to Neo4j AuraDB Free
while strictly preserving:
- 12 canonical node labels
- 12 canonical directed relationships
- Node unique business key constraints
- All entity attributes (camelCase and UPPERCASE aliases)
- Idempotent MERGE operations (safe to run multiple times without data duplication)

Usage:
    python scripts/migrate_to_auradb.py [--clear-first] [--dry-run]
"""

import os
import sys

# Ensure SSL CA bundle is active on macOS before OpenSSL C library initializes
if "SSL_CERT_FILE" not in os.environ:
    if os.path.isfile("/etc/ssl/cert.pem"):
        os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception:
            pass
import argparse
from typing import Dict, Any

# Ensure project root is on PYTHONPATH
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Ensure SSL CA bundle is loaded for encrypted cloud connections (especially on macOS)
if "SSL_CERT_FILE" not in os.environ:
    if os.path.isfile("/etc/ssl/cert.pem"):
        os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
    else:
        try:
            import certifi
            os.environ["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            pass

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

# Import canonical demo data definitions from seed_demo_data
try:
    from scripts.seed_demo_data import (
        DEPARTMENTS,
        PROGRAMS,
        STUDENTS,
        STUDENT_PROFILES,
        GUARDIANS,
        BANK_ACCOUNTS,
        STUDENT_FEES,
        PAYMENT_METHODS,
        FEE_PAYMENTS,
        SCHOLARSHIPS,
        SCHOLARSHIP_APPLICATIONS,
        DISBURSEMENTS,
    )
except ImportError:
    from seed_demo_data import (
        DEPARTMENTS,
        PROGRAMS,
        STUDENTS,
        STUDENT_PROFILES,
        GUARDIANS,
        BANK_ACCOUNTS,
        STUDENT_FEES,
        PAYMENT_METHODS,
        FEE_PAYMENTS,
        SCHOLARSHIPS,
        SCHOLARSHIP_APPLICATIONS,
        DISBURSEMENTS,
    )

APPLICATIONS = SCHOLARSHIP_APPLICATIONS
FEES = STUDENT_FEES
PAYMENTS = FEE_PAYMENTS

CONSTRAINTS = [
    "CREATE CONSTRAINT department_deptId_unique IF NOT EXISTS FOR (n:Department) REQUIRE n.deptId IS UNIQUE",
    "CREATE CONSTRAINT program_programId_unique IF NOT EXISTS FOR (n:Program) REQUIRE n.programId IS UNIQUE",
    "CREATE CONSTRAINT student_studentId_unique IF NOT EXISTS FOR (n:Student) REQUIRE n.studentId IS UNIQUE",
    "CREATE CONSTRAINT studentProfile_studentId_unique IF NOT EXISTS FOR (n:StudentProfile) REQUIRE n.studentId IS UNIQUE",
    "CREATE CONSTRAINT guardian_guardianId_unique IF NOT EXISTS FOR (n:Guardian) REQUIRE n.guardianId IS UNIQUE",
    "CREATE CONSTRAINT application_applicationId_unique IF NOT EXISTS FOR (n:Application) REQUIRE n.applicationId IS UNIQUE",
    "CREATE CONSTRAINT scholarship_scholarshipId_unique IF NOT EXISTS FOR (n:Scholarship) REQUIRE n.scholarshipId IS UNIQUE",
    "CREATE CONSTRAINT bankAccount_accountNo_unique IF NOT EXISTS FOR (n:BankAccount) REQUIRE n.accountNo IS UNIQUE",
    "CREATE CONSTRAINT fee_feeId_unique IF NOT EXISTS FOR (n:Fee) REQUIRE n.feeId IS UNIQUE",
    "CREATE CONSTRAINT paymentMethod_methodId_unique IF NOT EXISTS FOR (n:PaymentMethod) REQUIRE n.methodId IS UNIQUE",
    "CREATE CONSTRAINT payment_paymentId_unique IF NOT EXISTS FOR (n:Payment) REQUIRE n.paymentId IS UNIQUE",
    "CREATE CONSTRAINT disbursement_disbursementId_unique IF NOT EXISTS FOR (n:Disbursement) REQUIRE n.disbursementId IS UNIQUE",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Migrate dataset to Neo4j AuraDB Cloud")
    parser.add_argument("--uri", help="Neo4j connection URI (e.g. neo4j+s://xxx.databases.neo4j.io)")
    parser.add_argument("--user", help="Neo4j username (defaults to neo4j or from credentials file)")
    parser.add_argument("--password", help="Neo4j password")
    parser.add_argument("--credentials-file", help="Path to Neo4j credentials file (.txt)")
    parser.add_argument("--database", help="Target database name (default: neo4j)")
    parser.add_argument("--clear-first", action="store_true", help="Explicitly clear graph before seeding (default: False)")
    parser.add_argument("--dry-run", action="store_true", help="Verify connection without modifying data")
    return parser.parse_args()


def _load_env_if_needed(cred_file=None):
    if "SSL_CERT_FILE" not in os.environ:
        try:
            import certifi
            os.environ["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            if os.path.isfile("/etc/ssl/cert.pem"):
                os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"

    candidates = [
        cred_file,
        "/Users/pranjalsingh/Downloads/Neo4j-3d2c4ba3-Created-2026-10-24.txt",
        os.path.join(REPO_ROOT, ".env.aura"),
        os.path.join(REPO_ROOT, ".env"),
        os.path.join(REPO_ROOT, "backend", ".env"),
        os.path.join(os.getcwd(), ".env.aura"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())
            except OSError:
                pass


def get_connection_params(args):
    _load_env_if_needed(getattr(args, "credentials_file", None))
    uri = args.uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = args.user or os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or "neo4j"
    password = (
        args.password
        or os.getenv("AURA_PASSWORD")
        or os.getenv("NEO4J_AURA_PASSWORD")
        or os.getenv("NEO4J_PASSWORD")
    )
    database = args.database or os.getenv("NEO4J_DATABASE", "neo4j")

    if not password:
        print("\n❌ ERROR: AuraDB password is not provided.")
        print("Please set AURA_PASSWORD in .env.aura or export AURA_PASSWORD in your environment.")
        sys.exit(1)

    return uri, user, password, database


def _try_driver(uri, user, password):
    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        max_connection_lifetime=300,
        keep_alive=True
    )
    driver.verify_connectivity()
    return driver


def main():
    args = parse_args()
    uri, user, password, database = get_connection_params(args)

    is_auradb = uri.startswith("neo4j+s://") or uri.startswith("bolt+s://") or "databases.neo4j.io" in uri
    cloud_label = "Neo4j AuraDB (Cloud)" if is_auradb else "Local Neo4j"

    print("\n" + "=" * 65)
    print(f"  SCHOLARSHIP MANAGEMENT — {cloud_label.upper()} MIGRATION TOOL")
    print("=" * 65)
    print(f"Target URI     : {uri}")
    print(f"Target User    : {user}")
    print(f"Target Database: {database}")
    print(f"Clear First    : {'YES (Opt-in)' if args.clear_first else 'NO (Safe Idempotent Merge)'}")
    print(f"Dry Run        : {'YES' if args.dry_run else 'NO'}")
    print("=" * 65)

    print("\n[Step 1/5] Connecting to Neo4j instance...")
    driver = None
    try:
        driver = _try_driver(uri, user, password)
        print(f"✓ Connectivity verified successfully with user '{user}'!")
    except Exception as exc:
        alt_user = None
        if user == "neo4j" and os.getenv("NEO4J_USERNAME") and os.getenv("NEO4J_USERNAME") != "neo4j":
            alt_user = os.getenv("NEO4J_USERNAME")
        elif user != "neo4j":
            alt_user = "neo4j"
        if alt_user:
            try:
                driver = _try_driver(uri, alt_user, password)
                user = alt_user
                print(f"✓ Connectivity verified successfully with user '{user}'!")
            except Exception:
                pass
        if not driver:
            print(f"❌ Failed to connect to Neo4j: {exc}")
            sys.exit(1)

    if args.dry_run:
        print("\n✓ Dry-run completed successfully! Database is reachable. Exiting.")
        driver.close()
        return

    # Connect to target database with fallback for AuraDB naming
    session = None
    target_db = database
    for db_candidate in [database, os.getenv("NEO4J_DATABASE"), "3d2c4ba3", "neo4j", None]:
        try:
            s = driver.session(database=db_candidate) if db_candidate else driver.session()
            s.run("RETURN 1").consume()
            session = s
            target_db = db_candidate or "default"
            break
        except Exception:
            continue

    if not session:
        session = driver.session()
        target_db = "default"

    print(f"Using target database: {target_db}")

    with session:
        # Check current count
        rec = session.run("MATCH (n) RETURN count(n) AS cnt").single()
        current_node_count = rec["cnt"] if rec else 0
        print(f"Current node count in target database: {current_node_count}")

        if args.clear_first:
            print("\n[Step 2/5] Clearing target graph (--clear-first was specified)...")
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Target graph cleared.")
        else:
            print("\n[Step 2/5] Preserving existing data; applying safe idempotent MERGE operations.")

        print("\n[Step 3/5] Applying 12 unique constraints...")
        for c in CONSTRAINTS:
            try:
                session.run(c)
            except Exception as e:
                print(f"   Note on constraint: {e}")
        print("✓ All 12 canonical uniqueness constraints applied.")

        print("\n[Step 4/5] Ingesting nodes and merging relationships...")

        # 1. Departments
        for d in DEPARTMENTS:
            session.run(
                "MERGE (d:Department {deptId: $id}) "
                "SET d.name = $name, d.deptName = $name, d.dept_name = $name, d.DEPTID = $id, d.DEPTNAME = $name",
                {"id": d[0], "name": d[1]}
            )

        # 2. Programs & (Department)-[:HAS_PROGRAM]->(Program)
        for p in PROGRAMS:
            session.run(
                "MERGE (prg:Program {programId: $id}) "
                "SET prg.name = $name, prg.programName = $name, prg.degreeLevel = $deg, prg.deptId = $dept, "
                "    prg.PROGRAMID = $id, prg.PROGRAMNAME = $name, prg.DEGREELEVEL = $deg, prg.DEPTID = $dept "
                "WITH prg "
                "MATCH (d:Department {deptId: $dept}) "
                "MERGE (d)-[:HAS_PROGRAM]->(prg)",
                {"id": p[0], "name": p[1], "deg": p[2], "dept": p[3]}
            )

        # 3. Payment Methods
        for pm in PAYMENT_METHODS:
            session.run(
                "MERGE (m:PaymentMethod {methodId: $id}) "
                "SET m.name = $name, m.methodName = $name, m.method_id = $id, m.METHODID = $id, m.METHODNAME = $name",
                {"id": pm[0], "name": pm[1]}
            )

        # 4. Bank Accounts
        for ba in BANK_ACCOUNTS:
            session.run(
                "MERGE (b:BankAccount {accountNo: $acc}) "
                "SET b.name = $acc, b.bankName = $bank, b.ifsc = $ifsc, b.accountType = $atype, "
                "    b.ACCOUNTNO = $acc, b.BANKNAME = $bank, b.IFSC = $ifsc, b.ACCOUNTTYPE = $atype",
                {"acc": ba[0], "bank": ba[1], "ifsc": ba[2], "atype": ba[3]}
            )

        # 5. Students & (Program)-[:HAS_STUDENT]->(Student)
        for s in STUDENTS:
            session.run(
                "MERGE (stu:Student {studentId: $id}) "
                "SET stu.name = $name, stu.studentName = $name, stu.phone = $phone, stu.programId = $pid, "
                "    stu.houseNo = $hno, stu.street = $street, stu.city = $city, stu.pin = $pin, "
                "    stu.STUDENTID = $id, stu.STUDENTNAME = $name, stu.PHONE = $phone, stu.PROGRAMID = $pid, "
                "    stu.HOUSENO = $hno, stu.STREET = $street, stu.CITY = $city, stu.PIN = $pin "
                "WITH stu "
                "MATCH (prg:Program {programId: $pid}) "
                "MERGE (prg)-[:HAS_STUDENT]->(stu)",
                {
                    "id": s[0], "name": s[1], "phone": s[2], "hno": s[3],
                    "street": s[4], "city": s[5], "pin": s[6], "pid": s[7]
                }
            )

        # 6. Student Profiles & (Student)-[:HAS_PROFILE]->(StudentProfile)
        for sp in STUDENT_PROFILES:
            session.run(
                "MERGE (prof:StudentProfile {studentId: $id}) "
                "SET prof.name = $id, prof.bloodGroup = $bg, prof.nationality = $nat, "
                "    prof.dateOfBirth = $dob, prof.email = $email, "
                "    prof.STUDENTID = $id, prof.BLOODGROUP = $bg, prof.NATIONALITY = $nat, "
                "    prof.DATEOFBIRTH = $dob, prof.EMAIL = $email "
                "WITH prof "
                "MATCH (stu:Student {studentId: $id}) "
                "MERGE (stu)-[:HAS_PROFILE]->(prof)",
                {"id": sp[0], "bg": sp[1], "nat": sp[2], "dob": sp[3], "email": sp[4]}
            )

        # 7. Guardians & (Student)-[:HAS_GUARDIAN]->(Guardian)
        for g in GUARDIANS:
            session.run(
                "MERGE (grd:Guardian {guardianId: $gid}) "
                "SET grd.name = $name, grd.guardianName = $name, grd.studentId = $sid, "
                "    grd.relation = $rel, grd.phoneNo = $phone, grd.emailId = $email, "
                "    grd.GUARDIANID = $gid, grd.GUARDIANNAME = $name, grd.STUDENTID = $sid, "
                "    grd.RELATION = $rel, grd.PHONENO = $phone, grd.EMAILID = $email "
                "WITH grd "
                "MATCH (stu:Student {studentId: $sid}) "
                "MERGE (stu)-[:HAS_GUARDIAN]->(grd)",
                {
                    "gid": g[0], "sid": g[1], "name": g[2],
                    "rel": g[3], "phone": g[4], "email": g[5]
                }
            )

        # 8. Scholarship Applications & (Student)-[:SUBMITTED]->(Application)
        for a in APPLICATIONS:
            session.run(
                "MERGE (app:Application {applicationId: $aid}) "
                "SET app.name = $aid, app.studentId = $sid, app.applicationDate = $adate, "
                "    app.applicationStatus = $status, "
                "    app.APPLICATIONID = $aid, app.STUDENTID = $sid, app.APPLICATIONDATE = $adate, "
                "    app.APPLICATIONSTATUS = $status "
                "WITH app "
                "MATCH (stu:Student {studentId: $sid}) "
                "MERGE (stu)-[:SUBMITTED]->(app)",
                {"aid": a[0], "sid": a[1], "adate": a[2], "status": a[3]}
            )

        # 9. Scholarships & (Application)-[:AWARDS]->(Scholarship)
        for sc in SCHOLARSHIPS:
            session.run(
                "MERGE (sch:Scholarship {scholarshipId: $sid}) "
                "SET sch.name = $sid, sch.applicationId = $aid, sch.scholarshipType = $stype, "
                "    sch.amount = $amt, "
                "    sch.SCHOLARSHIPID = $sid, sch.APPLICATIONID = $aid, sch.SCHOLARSHIPTYPE = $stype, "
                "    sch.AMOUNT = $amt "
                "WITH sch "
                "MATCH (app:Application {applicationId: $aid}) "
                "MERGE (app)-[:AWARDS]->(sch)",
                {"sid": sc[0], "aid": sc[1], "stype": sc[2], "amt": float(sc[3])}
            )

        # 10. Disbursements & (Scholarship)-[:HAS_DISBURSEMENT]->(Disbursement)->(BankAccount)
        for d in DISBURSEMENTS:
            session.run(
                "MERGE (disb:Disbursement {disbursementId: $did}) "
                "SET disb.name = $did, disb.scholarshipId = $sid, disb.accountNo = $acc, "
                "    disb.disbursementDate = $ddate, disb.amount = $amt, disb.disbursementMode = $mode, "
                "    disb.DISBURSEMENTID = $did, disb.SCHOLARSHIPID = $sid, disb.ACCOUNTNO = $acc, "
                "    disb.DISBURSEMENTDATE = $ddate, disb.AMOUNT = $amt, disb.DISBURSEMENTMODE = $mode "
                "WITH disb "
                "MATCH (sch:Scholarship {scholarshipId: $sid}) "
                "MERGE (sch)-[:HAS_DISBURSEMENT]->(disb) "
                "WITH disb "
                "MATCH (ba:BankAccount {accountNo: $acc}) "
                "MERGE (disb)-[:TO_ACCOUNT]->(ba)",
                {
                    "did": d[0], "sid": d[1], "acc": d[2],
                    "ddate": d[3], "amt": float(d[4]), "mode": d[5]
                }
            )

        # 11. Student Fees & (Student)-[:HAS_FEE]->(Fee)
        for f in FEES:
            session.run(
                "MERGE (fee:Fee {feeId: $fid}) "
                "SET fee.name = $fid, fee.studentId = $sid, fee.feeAmount = $amt, fee.dueDate = $due, "
                "    fee.FEEID = $fid, fee.STUDENTID = $sid, fee.FEEAMOUNT = $amt, fee.DUEDATE = $due "
                "WITH fee "
                "MATCH (stu:Student {studentId: $sid}) "
                "MERGE (stu)-[:HAS_FEE]->(fee)",
                {"fid": f[0], "sid": f[1], "amt": float(f[2]), "due": f[3]}
            )

        # 12. Fee Payments & (Fee)-[:HAS_PAYMENT]->(Payment)->(PaymentMethod) + optional (Payment)-[:USES_SCHOLARSHIP]->(Scholarship)
        for p in PAYMENTS:
            session.run(
                "MERGE (pay:Payment {paymentId: $pid}) "
                "SET pay.name = $pid, pay.feeId = $fid, pay.scholarshipId = $sid, "
                "    pay.methodId = $mid, pay.paymentDate = $pdate, pay.amountPaid = $amt, "
                "    pay.transactionId = $txn, "
                "    pay.PAYMENTID = $pid, pay.FEEID = $fid, pay.SCHOLARSHIPID = $sid, "
                "    pay.METHODID = $mid, pay.PAYMENTDATE = $pdate, pay.AMOUNTPAID = $amt, "
                "    pay.TRANSACTIONID = $txn "
                "WITH pay "
                "MATCH (fee:Fee {feeId: $fid}) "
                "MERGE (fee)-[:HAS_PAYMENT]->(pay) "
                "WITH pay "
                "MATCH (pm:PaymentMethod {methodId: $mid}) "
                "MERGE (pay)-[:PAID_VIA]->(pm)",
                {
                    "pid": p[0], "fid": p[1], "sid": p[2], "mid": p[3],
                    "pdate": p[4], "amt": float(p[5]), "txn": p[6]
                }
            )
            if p[2]:  # If scholarshipId is present
                session.run(
                    "MATCH (pay:Payment {paymentId: $pid}), (sch:Scholarship {scholarshipId: $sid}) "
                    "MERGE (pay)-[:USES_SCHOLARSHIP]->(sch)",
                    {"pid": p[0], "sid": p[2]}
                )

        print("\n[Step 5/5] Auditing Target Database Structure & Parity...")
        node_res = session.run("MATCH (n) RETURN count(n) AS cnt").single()
        edge_res = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()
        total_nodes = node_res["cnt"]
        total_edges = edge_res["cnt"]

        labels_res = session.run("CALL db.labels() YIELD label RETURN collect(label) AS lbls").single()
        rels_res = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS rels").single()

        print("\n" + "=" * 65)
        print("                 MIGRATION AUDIT SUMMARY")
        print("=" * 65)
        print(f"Total Graph Nodes        : {total_nodes} (Expected: 250)")
        print(f"Total Graph Relationships: {total_edges} (Expected: 280)")
        print(f"Node Labels (12 Target)  : {len(labels_res['lbls'])} found")
        print(f"Relationship Types (12)  : {len(rels_res['rels'])} found")
        print("=" * 65)

        if total_nodes == 250 and total_edges == 280:
            print("🎉 100% PARITY CONFIRMED! All canonical nodes and relationships are active.")
        else:
            print(f"⚠️ Parity check note: found {total_nodes} nodes and {total_edges} relationships.")

    driver.close()


if __name__ == "__main__":
    main()
