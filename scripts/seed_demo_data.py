#!/usr/bin/env python3
"""
Repeatable, idempotent demo-data seeding engine for the Scholarship & Fee Management System.
Populates both Oracle Relational Database (12 tables) and Neo4j Graph Database (12 node types)
with realistic, logically consistent academic and financial demonstration records aligned with DA-2 and DA-3.
"""

import os
import sys
import argparse

# Ensure repo root is on python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# -----------------------------------------------------------------------------
# CANONICAL DEMO DATASET (Aligned with DA-2 / DA-3 IDs)
# -----------------------------------------------------------------------------

DEPARTMENTS = [
    ("D01", "Computer Science"),
    ("D02", "Electronics"),
    ("D03", "Mechanical Engineering"),
    ("D04", "Artificial Intelligence & Data Science"),
    ("D05", "Biotechnology & Biomedical Engineering"),
]

PROGRAMS = [
    ("P01", "Computer Science and Engineering", "BTech", "D01"),
    ("P02", "Electronics and Communication Engineering", "BTech", "D02"),
    ("P03", "Mechanical Engineering", "BTech", "D03"),
    ("P04", "M.Tech Artificial Intelligence", "MTech", "D04"),
    ("P05", "B.Tech Data Science", "BTech", "D04"),
    ("P06", "M.Tech VLSI and Embedded Systems", "MTech", "D02"),
    ("P07", "B.Tech Robotics and Automation", "BTech", "D03"),
    ("P08", "M.Tech Thermal Engineering", "MTech", "D03"),
    ("P09", "B.Tech Biotechnology", "BTech", "D05"),
    ("P10", "PhD Computer Science & Systems", "PhD", "D01"),
]

PAYMENT_METHODS = [
    ("M01", "UPI"),
    ("M02", "Net Banking"),
    ("M03", "Credit Card"),
    ("M04", "Debit Card"),
    ("M05", "Demand Draft"),
]

BANK_ACCOUNTS = [
    ("AC001", "State Bank of India", "SBIN0001234", "Savings"),
    ("AC002", "HDFC Bank", "HDFC0001234", "Savings"),
    ("AC003", "ICICI Bank", "ICIC0001234", "Savings"),
    ("AC004", "Axis Bank", "UTIB0001234", "Savings"),
    ("AC005", "Punjab National Bank", "PUNB0001234", "Savings"),
    ("AC006", "State Bank of India", "SBIN0002345", "Savings"),
    ("AC007", "Bank of Baroda", "BARB0006789", "Savings"),
    ("AC008", "Canara Bank", "CNRB0001234", "Student Account"),
    ("AC009", "Union Bank of India", "UBIN0005678", "Savings"),
    ("AC010", "HDFC Bank", "HDFC0009012", "Savings"),
    ("AC011", "ICICI Bank", "ICIC0003456", "Student Account"),
    ("AC012", "Kotak Mahindra Bank", "KKBK0007890", "Savings"),
    ("AC013", "State Bank of India", "SBIN0004567", "Savings"),
    ("AC014", "Federal Bank", "FDRL0008901", "Student Account"),
    ("AC015", "Axis Bank", "UTIB0002345", "Savings"),
    ("AC016", "IndusInd Bank", "INDB0006789", "Savings"),
    ("AC017", "State Bank of India", "SBIN0007890", "Student Account"),
    ("AC018", "HDFC Bank", "HDFC0001234", "Savings"),
    ("AC019", "Punjab National Bank", "PUNB0005678", "Savings"),
    ("AC020", "IDFC First Bank", "IDFB0009012", "Student Account"),
    ("AC021", "State Bank of India", "SBIN0003456", "Savings"),
    ("AC022", "ICICI Bank", "ICIC0007890", "Savings"),
    ("AC023", "Bank of India", "BKID0001234", "Student Account"),
    ("AC024", "Axis Bank", "UTIB0005678", "Savings"),
    ("AC025", "Canara Bank", "CNRB0009012", "Savings"),
]

# 25 Students preserving original S001-S005
STUDENTS = [
    ("S001", "Aarav Sharma", "9876543210", "12A", "MG Road", "Chennai", "600001", "P01"),
    ("S002", "Priya Nair", "9876543211", "24B", "Anna Nagar", "Chennai", "600040", "P02"),
    ("S003", "Rahul Verma", "9876543212", "15C", "Gandhi Road", "Chennai", "600020", "P03"),
    ("S004", "Ananya Singh", "9876543213", "8D", "OMR Road", "Chennai", "600096", "P01"),
    ("S005", "Karan Patel", "9876543214", "17E", "Velachery Road", "Chennai", "600042", "P02"),
    ("S006", "Diya Patel", "9876543215", "House 12", "MG Road", "Ahmedabad", "380001", "P01"),
    ("S007", "Rohan Iyer", "9876543216", "Plot 77", "Anna Salai", "Chennai", "600002", "P04"),
    ("S008", "Ananya Gupta", "9876543217", "B-14", "Civil Lines", "New Delhi", "110054", "P04"),
    ("S009", "Vikram Malhotra", "9876543218", "Flat 101", "Bandra West", "Mumbai", "400050", "P05"),
    ("S010", "Sneha Nair", "9876543219", "Villa 5", "Kaloor", "Kochi", "682017", "P05"),
    ("S011", "Aditya Verma", "9876543220", "House 88", "Gomti Nagar", "Lucknow", "226010", "P06"),
    ("S012", "Pooja Reddy", "9876543221", "Plot 23", "Banjara Hills", "Hyderabad", "500034", "P06"),
    ("S013", "Siddharth Rao", "9876543222", "Flat 304", "Sadashivnagar", "Bangalore", "560080", "P07"),
    ("S014", "Meera Krishnan", "9876543223", "House 45", "T Nagar", "Chennai", "600017", "P07"),
    ("S015", "Kabir Mehta", "9876543224", "Flat 502", "Navrangpura", "Ahmedabad", "380009", "P08"),
    ("S016", "Riya Sengupta", "9876543225", "Tower C-12", "Salt Lake", "Kolkata", "700091", "P08"),
    ("S017", "Arjun Deshmukh", "9876543226", "House 19", "Shivajinagar", "Pune", "411005", "P09"),
    ("S018", "Ishita Joshi", "9876543227", "Plot 61", "Malviya Nagar", "Jaipur", "302017", "P09"),
    ("S019", "Tanmay Bhatia", "9876543228", "Flat 203", "Sector 18", "Chandigarh", "160018", "P01"),
    ("S020", "Priya Choudhury", "9876543229", "House 7", "Guwahati Club", "Guwahati", "781003", "P02"),
    ("S021", "Nikhil Kulkarni", "9876543230", "Flat 801", "Kothrud", "Pune", "411038", "P03"),
    ("S022", "Kavya Menon", "9876543231", "Villa 9", "Kowdiar", "Trivandrum", "695003", "P04"),
    ("S023", "Aman Kapoor", "9876543232", "House 31", "Model Town", "Ludhiana", "141002", "P05"),
    ("S024", "Shreya Das", "9876543233", "Plot 42", "Ballygunge", "Kolkata", "700019", "P07"),
    ("S025", "Harshit Tiwari", "9876543234", "Plot 99", "Civil Lines", "Kanpur", "208001", "P10"),
]

STUDENT_PROFILES = [
    ("S001", "O+", "Indian", "2006-05-14", "aarav@example.com"),
    ("S002", "A+", "Indian", "2005-11-22", "priya@example.com"),
    ("S003", "B+", "Indian", "2006-02-18", "rahul@example.com"),
    ("S004", "AB+", "Indian", "2006-08-30", "ananya@example.com"),
    ("S005", "O-", "Indian", "2005-12-10", "karan@example.com"),
    ("S006", "A+", "Indian", "2003-08-22", "diya.patel@campus.edu"),
    ("S007", "B+", "Indian", "2001-11-03", "rohan.iyer@campus.edu"),
    ("S008", "AB+", "Indian", "2003-02-18", "ananya.gupta@campus.edu"),
    ("S009", "O-", "Indian", "2002-09-30", "vikram.malhotra@campus.edu"),
    ("S010", "A-", "Indian", "2001-04-12", "sneha.nair@campus.edu"),
    ("S011", "B-", "Indian", "2003-07-25", "aditya.verma@campus.edu"),
    ("S012", "O+", "Indian", "2003-12-05", "pooja.reddy@campus.edu"),
    ("S013", "A+", "Indian", "2001-06-19", "siddharth.rao@campus.edu"),
    ("S014", "B+", "Indian", "2003-03-28", "meera.krishnan@campus.edu"),
    ("S015", "AB-", "Indian", "2002-10-15", "kabir.mehta@campus.edu"),
    ("S016", "O+", "Indian", "2001-01-20", "riya.sengupta@campus.edu"),
    ("S017", "A+", "Indian", "2001-08-11", "arjun.deshmukh@campus.edu"),
    ("S018", "B+", "Indian", "2003-09-04", "ishita.joshi@campus.edu"),
    ("S019", "O-", "Indian", "2003-06-17", "tanmay.bhatia@campus.edu"),
    ("S020", "A-", "Indian", "2003-01-29", "priya.choudhury@campus.edu"),
    ("S021", "B-", "Indian", "2001-12-14", "nikhil.kulkarni@campus.edu"),
    ("S022", "AB+", "Indian", "2003-04-08", "kavya.menon@campus.edu"),
    ("S023", "O+", "Indian", "2001-07-23", "aman.kapoor@campus.edu"),
    ("S024", "A+", "Indian", "2003-10-31", "shreya.das@campus.edu"),
    ("S025", "O+", "Indian", "1999-03-15", "harshit.tiwari@campus.edu"),
]

GUARDIANS = [
    ("G001", "S001", "Rajesh Sharma", "Father", "9876500001", "rajesh@example.com"),
    ("G002", "S002", "Suresh Nair", "Father", "9876500002", "suresh@example.com"),
    ("G003", "S003", "Manoj Verma", "Father", "9876500003", "manoj@example.com"),
    ("G004", "S004", "Sunita Singh", "Mother", "9876500004", "sunita@example.com"),
    ("G005", "S005", "Bhavin Patel", "Father", "9876500005", "bhavin@example.com"),
    ("G006", "S006", "Geeta Patel", "Mother", "9123456702", "geeta.patel@gmail.com"),
    ("G007", "S007", "Sundaram Iyer", "Father", "9123456703", "sundaram.iyer@gmail.com"),
    ("G008", "S008", "Rajesh Gupta", "Father", "9123456704", "rajesh.gupta@gmail.com"),
    ("G009", "S009", "Sunita Malhotra", "Mother", "9123456705", "sunita.malhotra@gmail.com"),
    ("G010", "S010", "K. Narayanan Nair", "Father", "9123456706", "kn.nair@gmail.com"),
    ("G011", "S011", "Alok Verma", "Father", "9123456707", "alok.verma@gmail.com"),
    ("G012", "S012", "Venkatesh Reddy", "Father", "9123456708", "venkat.reddy@gmail.com"),
    ("G013", "S013", "Anand Rao", "Father", "9123456709", "anand.rao@gmail.com"),
    ("G014", "S014", "Lakshmi Krishnan", "Mother", "9123456710", "lakshmi.k@gmail.com"),
    ("G015", "S015", "Deepak Mehta", "Father", "9123456711", "deepak.mehta@gmail.com"),
    ("G016", "S016", "Subhash Sengupta", "Father", "9123456712", "subhash.sg@gmail.com"),
    ("G017", "S017", "Prakash Deshmukh", "Father", "9123456713", "prakash.d@gmail.com"),
    ("G018", "S018", "Manish Joshi", "Father", "9123456714", "manish.joshi@gmail.com"),
    ("G019", "S019", "Harish Bhatia", "Father", "9123456715", "harish.bhatia@gmail.com"),
    ("G020", "S020", "Biren Choudhury", "Father", "9123456716", "biren.c@gmail.com"),
    ("G021", "S021", "Sanjay Kulkarni", "Father", "9123456717", "sanjay.k@gmail.com"),
    ("G022", "S022", "Radha Menon", "Mother", "9123456718", "radha.menon@gmail.com"),
    ("G023", "S023", "Vinod Kapoor", "Father", "9123456719", "vinod.kapoor@gmail.com"),
    ("G024", "S024", "Tapan Das", "Father", "9123456720", "tapan.das@gmail.com"),
    ("G025", "S025", "Brijesh Tiwari", "Father", "9123456725", "brijesh.tiwari@gmail.com"),
]

# 35 applications (preserving A001-A005)
SCHOLARSHIP_APPLICATIONS = [
    ("A001", "S001", "2026-01-10", "Approved"),
    ("A002", "S002", "2026-01-12", "Approved"),
    ("A003", "S003", "2026-01-15", "Approved"),
    ("A004", "S004", "2026-01-18", "Pending"),
    ("A005", "S005", "2026-01-20", "Approved"),
    ("A006", "S006", "2026-08-01", "Approved"),
    ("A007", "S007", "2026-08-02", "Approved"),
    ("A008", "S008", "2026-08-03", "Approved"),
    ("A009", "S009", "2026-08-04", "Approved"),
    ("A010", "S010", "2026-08-05", "Approved"),
    ("A011", "S011", "2026-08-06", "Pending"),
    ("A012", "S012", "2026-08-07", "Rejected"),
    ("A013", "S013", "2026-08-08", "Approved"),
    ("A014", "S014", "2026-08-09", "Pending"),
    ("A015", "S015", "2026-08-10", "Approved"),
    ("A016", "S016", "2026-08-11", "Pending"),
    ("A017", "S017", "2026-08-12", "Rejected"),
    ("A018", "S018", "2026-08-13", "Pending"),
    ("A019", "S019", "2026-08-14", "Approved"),
    ("A020", "S020", "2026-08-15", "Pending"),
    ("A021", "S021", "2026-08-16", "Approved"),
    ("A022", "S022", "2026-08-17", "Rejected"),
    ("A023", "S023", "2026-08-18", "Approved"),
    ("A024", "S024", "2026-08-19", "Pending"),
    ("A025", "S025", "2026-08-20", "Approved"),
    ("A026", "S001", "2026-09-01", "Approved"),
    ("A027", "S002", "2026-09-02", "Pending"),
    ("A028", "S003", "2026-09-03", "Approved"),
    ("A029", "S005", "2026-09-04", "Approved"),
    ("A030", "S007", "2026-09-05", "Pending"),
    ("A031", "S009", "2026-09-06", "Approved"),
    ("A032", "S013", "2026-09-07", "Pending"),
    ("A033", "S015", "2026-09-08", "Rejected"),
    ("A034", "S019", "2026-09-09", "Pending"),
    ("A035", "S025", "2026-09-10", "Approved"),
]

# 15 scholarships mapped to approved applications (preserving SCH001-SCH005)
SCHOLARSHIPS = [
    ("SCH001", "A001", "Merit", 50000),
    ("SCH002", "A002", "Need-based", 30000),
    ("SCH003", "A003", "Sports", 40000),
    ("SCH004", "A005", "Merit", 35000),
    ("SCH005", "A006", "Need-based", 45000),
    ("SCH006", "A007", "Departmental", 55000),
    ("SCH007", "A008", "Merit", 50000),
    ("SCH008", "A009", "Need-based", 40000),
    ("SCH009", "A010", "Sports", 30000),
    ("SCH010", "A013", "Departmental", 45000),
    ("SCH011", "A015", "Merit", 65000),
    ("SCH012", "A019", "Need-based", 35000),
    ("SCH013", "A021", "Research", 75000),
    ("SCH014", "A023", "Research", 80000),
    ("SCH015", "A025", "Merit", 25000),
]

# 18 disbursements (preserving DIS001-DIS004, using valid check constraint modes: 'Bank Transfer' / 'Direct Transfer')
DISBURSEMENTS = [
    ("DIS001", "SCH001", "AC001", "2026-02-10", 50000, "Bank Transfer"),
    ("DIS002", "SCH002", "AC002", "2026-02-02", 30000, "Direct Transfer"),
    ("DIS003", "SCH003", "AC003", "2026-02-15", 40000, "Bank Transfer"),
    ("DIS004", "SCH004", "AC005", "2026-02-20", 35000, "Bank Transfer"),
    ("DIS005", "SCH005", "AC006", "2026-08-20", 45000, "Direct Transfer"),
    ("DIS006", "SCH006", "AC007", "2026-08-25", 55000, "Bank Transfer"),
    ("DIS007", "SCH007", "AC008", "2026-09-01", 50000, "Direct Transfer"),
    ("DIS008", "SCH008", "AC009", "2026-09-05", 40000, "Bank Transfer"),
    ("DIS009", "SCH009", "AC010", "2026-09-10", 30000, "Direct Transfer"),
    ("DIS010", "SCH010", "AC013", "2026-09-12", 45000, "Bank Transfer"),
    ("DIS011", "SCH011", "AC015", "2026-09-15", 65000, "Direct Transfer"),
    ("DIS012", "SCH012", "AC019", "2026-09-18", 35000, "Bank Transfer"),
    ("DIS013", "SCH013", "AC021", "2026-09-20", 75000, "Direct Transfer"),
    ("DIS014", "SCH014", "AC023", "2026-09-22", 80000, "Bank Transfer"),
    ("DIS015", "SCH015", "AC025", "2026-09-25", 25000, "Direct Transfer"),
    ("DIS016", "SCH001", "AC001", "2026-10-01", 25000, "Bank Transfer"),
    ("DIS017", "SCH006", "AC007", "2026-10-05", 20000, "Direct Transfer"),
    ("DIS018", "SCH011", "AC015", "2026-10-10", 25000, "Bank Transfer"),
]

# 30 fees (preserving F001-F005)
STUDENT_FEES = [
    ("F001", "S001", 75000, "2026-03-01"),
    ("F002", "S002", 80000, "2026-03-01"),
    ("F003", "S003", 70000, "2026-03-01"),
    ("F004", "S004", 75000, "2026-03-01"),
    ("F005", "S005", 80000, "2026-03-01"),
    ("F006", "S006", 60000, "2026-08-30"),
    ("F007", "S007", 75000, "2026-08-30"),
    ("F008", "S008", 65000, "2026-08-30"),
    ("F009", "S009", 65000, "2026-08-30"),
    ("F010", "S010", 70000, "2026-08-30"),
    ("F011", "S011", 55000, "2026-08-30"),
    ("F012", "S012", 55000, "2026-08-30"),
    ("F013", "S013", 70000, "2026-08-30"),
    ("F014", "S014", 50000, "2026-08-30"),
    ("F015", "S015", 50000, "2026-08-30"),
    ("F016", "S016", 75000, "2026-08-30"),
    ("F017", "S017", 75000, "2026-08-30"),
    ("F018", "S018", 60000, "2026-08-30"),
    ("F019", "S019", 60000, "2026-08-30"),
    ("F020", "S020", 60000, "2026-08-30"),
    ("F021", "S021", 75000, "2026-08-30"),
    ("F022", "S022", 65000, "2026-08-30"),
    ("F023", "S023", 70000, "2026-08-30"),
    ("F024", "S024", 55000, "2026-08-30"),
    ("F025", "S025", 85000, "2026-08-30"),
    ("F026", "S001", 15000, "2026-10-15"),
    ("F027", "S002", 15000, "2026-10-15"),
    ("F028", "S003", 20000, "2026-10-15"),
    ("F029", "S005", 15000, "2026-10-15"),
    ("F030", "S007", 20000, "2026-10-15"),
]

# 32 payments (preserving PAY001-PAY005). Total paid for any FeeID <= FeeAmount.
FEE_PAYMENTS = [
    # S001 F001 (75,000) - Paid in 2 installments (25,000 + 10,000 = 35,000 - Partial)
    ("PAY001", "F001", "SCH001", "M01", "2026-02-25", 25000, "TXN1001"),
    ("PAY005", "F001", None, "M01", "2026-03-02", 10000, "TXN1005"),

    # S002 F002 (80,000) - Paid in 1 installment (20,000 - Partial)
    ("PAY002", "F002", "SCH002", "M02", "2026-02-26", 20000, "TXN1002"),

    # S003 F003 (70,000) - Paid in 1 installment (30,000 - Partial)
    ("PAY003", "F003", "SCH003", "M03", "2026-02-27", 30000, "TXN1003"),

    # S004 F004 (75,000) - Overdue / Unpaid (0 payments)

    # S005 F005 (80,000) - Paid in 1 installment (15,000 - Partial)
    ("PAY004", "F005", "SCH004", "M04", "2026-02-28", 15000, "TXN1004"),

    # S006 F006 (60,000) - Fully settled (60,000)
    ("PAY006", "F006", "SCH005", "M01", "2026-08-10", 60000, "TXN1006"),

    # S007 F007 (75,000) - Paid in 2 installments (40,000 + 35,000 = 75,000 - Fully settled)
    ("PAY007", "F007", "SCH006", "M02", "2026-08-12", 40000, "TXN1007"),
    ("PAY008", "F007", None, "M01", "2026-08-25", 35000, "TXN1008"),

    # S008 F008 (65,000) - Partially paid (30,000 paid)
    ("PAY009", "F008", "SCH007", "M03", "2026-08-14", 30000, "TXN1009"),

    # S009 F009 (65,000) - Fully settled (65,000)
    ("PAY010", "F009", "SCH008", "M01", "2026-08-18", 65000, "TXN1010"),

    # S010 F010 (70,000) - Partially paid (35,000 paid)
    ("PAY011", "F010", "SCH009", "M02", "2026-08-20", 35000, "TXN1011"),

    # S011 F011 (55,000) - Overdue / Unpaid

    # S012 F012 (55,000) - Partially paid (15,000 paid)
    ("PAY012", "F012", None, "M01", "2026-08-22", 15000, "TXN1012"),

    # S013 F013 (70,000) - Fully settled (40,000 + 30,000)
    ("PAY013", "F013", "SCH010", "M02", "2026-08-24", 40000, "TXN1013"),
    ("PAY014", "F013", None, "M01", "2026-09-01", 30000, "TXN1014"),

    # S014 F014 (50,000) - Fully settled (50,000)
    ("PAY015", "F014", None, "M01", "2026-08-26", 50000, "TXN1015"),

    # S015 F015 (50,000) - Partially paid (20,000 paid)
    ("PAY016", "F015", "SCH011", "M04", "2026-08-28", 20000, "TXN1016"),

    # S016 F016 (75,000) - Overdue / Unpaid

    # S017 F017 (75,000) - Fully settled (45,000 + 30,000)
    ("PAY017", "F017", None, "M02", "2026-08-29", 45000, "TXN1017"),
    ("PAY018", "F017", None, "M01", "2026-09-05", 30000, "TXN1018"),

    # S018 F018 (60,000) - Partially paid (25,000 paid)
    ("PAY019", "F018", None, "M01", "2026-09-02", 25000, "TXN1019"),

    # S019 F019 (60,000) - Fully settled (60,000)
    ("PAY020", "F019", "SCH012", "M03", "2026-09-04", 60000, "TXN1020"),

    # S020 F020 (60,000) - Partially paid (30,000 paid)
    ("PAY021", "F020", None, "M01", "2026-09-06", 30000, "TXN1021"),

    # S021 F021 (75,000) - Fully settled (45,000 + 30,000)
    ("PAY022", "F021", "SCH013", "M02", "2026-09-08", 45000, "TXN1022"),
    ("PAY023", "F021", None, "M01", "2026-09-15", 30000, "TXN1023"),

    # S022 F022 (65,000) - Overdue / Unpaid

    # S023 F023 (70,000) - Fully settled (70,000)
    ("PAY024", "F023", "SCH014", "M05", "2026-09-10", 70000, "TXN1024"),

    # S024 F024 (55,000) - Partially paid (25,000 paid)
    ("PAY025", "F024", None, "M01", "2026-09-12", 25000, "TXN1025"),

    # S025 F025 (85,000) - Fully settled (85,000)
    ("PAY026", "F025", "SCH015", "M02", "2026-09-22", 85000, "TXN1026"),

    # Additional term fee payments
    ("PAY027", "F026", None, "M01", "2026-10-10", 15000, "TXN1027"),
    ("PAY028", "F027", None, "M02", "2026-10-11", 15000, "TXN1028"),
    ("PAY029", "F028", None, "M01", "2026-10-12", 20000, "TXN1029"),
    ("PAY030", "F029", None, "M03", "2026-10-13", 15000, "TXN1030"),
    ("PAY031", "F030", None, "M01", "2026-10-14", 10000, "TXN1031"),
    ("PAY032", "F001", None, "M01", "2026-10-15", 40000, "TXN1032"),
]


# -----------------------------------------------------------------------------
# ORACLE SEEDING ADAPTER
# -----------------------------------------------------------------------------

def seed_oracle():
    """Seed Oracle database with canonical demo data."""
    try:
        from backend.db import get_connection
    except ModuleNotFoundError:
        from db import get_connection

    print("\n=======================================================")
    print("  SEEDING ORACLE RELATIONAL DATABASE")
    print("=======================================================")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("-> Clearing existing dependent data...")
        tables_to_clear = [
            "FEE_PAYMENT", "DISBURSEMENT", "STUDENT_FEE", "SCHOLARSHIP",
            "SCHOLARSHIP_APPLICATION", "GUARDIAN", "STUDENT_PROFILE",
            "STUDENT", "BANK_ACCOUNT", "PROGRAM", "DEPARTMENT", "PAYMENT_METHOD"
        ]
        for t in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {t}")
            except Exception as e:
                print(f"   Note clearing {t}: {e}")

        conn.commit()
        print("-> Inserting canonical demo data...")

        # 1. DEPARTMENT
        cursor.executemany(
            "INSERT INTO DEPARTMENT (DeptID, DeptName) VALUES (:1, :2)",
            DEPARTMENTS
        )

        # 2. PROGRAM
        cursor.executemany(
            "INSERT INTO PROGRAM (ProgramID, ProgramName, DegreeLevel, DeptID) VALUES (:1, :2, :3, :4)",
            PROGRAMS
        )

        # 3. PAYMENT_METHOD
        cursor.executemany(
            "INSERT INTO PAYMENT_METHOD (MethodID, MethodName) VALUES (:1, :2)",
            PAYMENT_METHODS
        )

        # 4. BANK_ACCOUNT
        cursor.executemany(
            "INSERT INTO BANK_ACCOUNT (AccountNo, BankName, IFSC, AccountType) VALUES (:1, :2, :3, :4)",
            BANK_ACCOUNTS
        )

        # 5. STUDENT
        cursor.executemany(
            "INSERT INTO STUDENT (StudentID, StudentName, Phone, HouseNo, Street, City, PIN, ProgramID) "
            "VALUES (:1, :2, :3, :4, :5, :6, :7, :8)",
            STUDENTS
        )

        # 6. STUDENT_PROFILE
        cursor.executemany(
            "INSERT INTO STUDENT_PROFILE (StudentID, BloodGroup, Nationality, DateOfBirth, Email) "
            "VALUES (:1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD'), :5)",
            STUDENT_PROFILES
        )

        # 7. GUARDIAN
        cursor.executemany(
            "INSERT INTO GUARDIAN (GuardianID, StudentID, GuardianName, Relation, PhoneNo, EmailID) "
            "VALUES (:1, :2, :3, :4, :5, :6)",
            GUARDIANS
        )

        # 8. SCHOLARSHIP_APPLICATION
        cursor.executemany(
            "INSERT INTO SCHOLARSHIP_APPLICATION (ApplicationID, StudentID, ApplicationDate, ApplicationStatus) "
            "VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), :4)",
            SCHOLARSHIP_APPLICATIONS
        )

        # 9. SCHOLARSHIP
        cursor.executemany(
            "INSERT INTO SCHOLARSHIP (ScholarshipID, ApplicationID, ScholarshipType, Amount) "
            "VALUES (:1, :2, :3, :4)",
            SCHOLARSHIPS
        )

        # 10. DISBURSEMENT
        cursor.executemany(
            "INSERT INTO DISBURSEMENT (DisbursementID, ScholarshipID, AccountNo, DisbursementDate, Amount, DisbursementMode) "
            "VALUES (:1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD'), :5, :6)",
            DISBURSEMENTS
        )

        # 11. STUDENT_FEE
        cursor.executemany(
            "INSERT INTO STUDENT_FEE (FeeID, StudentID, FeeAmount, DueDate) "
            "VALUES (:1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD'))",
            STUDENT_FEES
        )

        # 12. FEE_PAYMENT (Disable trigger during batch seed to avoid mutating table error, then enable)
        try:
            cursor.execute("ALTER TRIGGER TRG_CHECK_FEE_PAYMENT DISABLE")
        except Exception:
            pass

        for p in FEE_PAYMENTS:
            cursor.execute(
                "INSERT INTO FEE_PAYMENT (PaymentID, FeeID, ScholarshipID, MethodID, PaymentDate, AmountPaid, TransactionID) "
                "VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'), :6, :7)",
                p
            )

        try:
            cursor.execute("ALTER TRIGGER TRG_CHECK_FEE_PAYMENT ENABLE")
        except Exception:
            pass

        conn.commit()
        print("✓ Oracle database seeded successfully!")

        print("\nOracle Record Counts Summary:")
        for t in tables_to_clear:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t:25}: {cursor.fetchone()[0]:4} records")

    except Exception as e:
        conn.rollback()
        print(f"❌ Oracle seeding error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


# -----------------------------------------------------------------------------
# NEO4J SEEDING ADAPTER
# -----------------------------------------------------------------------------

def seed_neo4j():
    """Seed Neo4j graph database with canonical demo entities and relationships."""
    try:
        from backend.neo4j_db import get_driver, get_database_name
    except ModuleNotFoundError:
        from neo4j_db import get_driver, get_database_name

    print("\n=======================================================")
    print("  SEEDING NEO4J GRAPH DATABASE")
    print("=======================================================")

    driver = get_driver()
    db = get_database_name()

    with driver.session(database=db) as session:
        print("-> Clearing existing graph data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("-> Ensuring constraints and indexes on canonical camelCase identifiers...")
        constraints = [
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
        for c in constraints:
            try:
                session.run(c)
            except Exception as e:
                print(f"   Constraint note: {e}")

        print("-> Merging canonical graph nodes & relationships...")

        # 1. Departments
        for d in DEPARTMENTS:
            session.run(
                "MERGE (d:Department {deptId: $id}) "
                "SET d.name = $name, d.deptName = $name, d.dept_name = $name",
                {"id": d[0], "name": d[1]}
            )

        # 2. Programs & (Department)-[:HAS_PROGRAM]->(Program)
        for p in PROGRAMS:
            session.run(
                "MERGE (prg:Program {programId: $id}) "
                "SET prg.name = $name, prg.programName = $name, prg.degreeLevel = $deg, prg.deptId = $dept "
                "WITH prg "
                "MATCH (d:Department {deptId: $dept}) "
                "MERGE (d)-[:HAS_PROGRAM]->(prg)",
                {"id": p[0], "name": p[1], "deg": p[2], "dept": p[3]}
            )

        # 3. Payment Methods
        for pm in PAYMENT_METHODS:
            session.run(
                "MERGE (m:PaymentMethod {methodId: $id}) "
                "SET m.name = $name, m.methodName = $name, m.method_id = $id",
                {"id": pm[0], "name": pm[1]}
            )

        # 4. Bank Accounts
        for ba in BANK_ACCOUNTS:
            session.run(
                "MERGE (b:BankAccount {accountNo: $acc}) "
                "SET b.name = $acc, b.bankName = $bank, b.ifsc = $ifsc, b.accountType = $atype, b.account_no = $acc",
                {"acc": ba[0], "bank": ba[1], "ifsc": ba[2], "atype": ba[3]}
            )

        # 5. Students & (Program)-[:HAS_STUDENT]->(Student)
        for s in STUDENTS:
            session.run(
                "MERGE (st:Student {studentId: $id}) "
                "SET st.name = $name, st.studentName = $name, st.phone = $phone, "
                "    st.houseNo = $house, st.street = $street, st.city = $city, st.pin = $pin, st.programId = $prg, "
                "    st.student_id = $id, st.student_name = $name "
                "WITH st "
                "MATCH (p:Program {programId: $prg}) "
                "MERGE (p)-[:HAS_STUDENT]->(st)",
                {
                    "id": s[0], "name": s[1], "phone": s[2],
                    "house": s[3], "street": s[4], "city": s[5], "pin": s[6], "prg": s[7]
                }
            )

        # 6. Student Profiles & (Student)-[:HAS_PROFILE]->(StudentProfile)
        for sp in STUDENT_PROFILES:
            session.run(
                "MERGE (prof:StudentProfile {studentId: $id}) "
                "SET prof.bloodGroup = $blood, prof.nationality = $nat, prof.dateOfBirth = $dob, prof.email = $email "
                "WITH prof "
                "MATCH (st:Student {studentId: $id}) "
                "MERGE (st)-[:HAS_PROFILE]->(prof)",
                {"id": sp[0], "blood": sp[1], "nat": sp[2], "dob": sp[3], "email": sp[4]}
            )

        # 7. Guardians & (Student)-[:HAS_GUARDIAN]->(Guardian)
        for g in GUARDIANS:
            session.run(
                "MERGE (grd:Guardian {guardianId: $gid}) "
                "SET grd.name = $name, grd.guardianName = $name, grd.relation = $rel, grd.phoneNo = $phone, grd.emailId = $email, grd.studentId = $sid "
                "WITH grd "
                "MATCH (st:Student {studentId: $sid}) "
                "MERGE (st)-[:HAS_GUARDIAN]->(grd)",
                {"gid": g[0], "sid": g[1], "name": g[2], "rel": g[3], "phone": g[4], "email": g[5]}
            )

        # 8. Applications & (Student)-[:SUBMITTED]->(Application)
        for app in SCHOLARSHIP_APPLICATIONS:
            session.run(
                "MERGE (a:Application {applicationId: $aid}) "
                "SET a.name = $aid, a.applicationDate = $adate, a.status = $status, a.studentId = $sid "
                "WITH a "
                "MATCH (st:Student {studentId: $sid}) "
                "MERGE (st)-[:SUBMITTED]->(a)",
                {"aid": app[0], "sid": app[1], "adate": app[2], "status": app[3]}
            )

        # 9. Scholarships & (Application)-[:AWARDS]->(Scholarship)
        for sch in SCHOLARSHIPS:
            session.run(
                "MERGE (sc:Scholarship {scholarshipId: $sid}) "
                "SET sc.name = $sid, sc.scholarshipType = $type, sc.amount = $amt, sc.applicationId = $aid "
                "WITH sc "
                "MATCH (a:Application {applicationId: $aid}) "
                "MERGE (a)-[:AWARDS]->(sc)",
                {"sid": sch[0], "aid": sch[1], "type": sch[2], "amt": sch[3]}
            )

        # 10. Disbursements & (Scholarship)-[:HAS_DISBURSEMENT]->(Disbursement)-[:TO_ACCOUNT]->(BankAccount)
        for ds in DISBURSEMENTS:
            session.run(
                "MERGE (d:Disbursement {disbursementId: $did}) "
                "SET d.name = $did, d.amount = $amt, d.disbursementDate = $ddate, d.disbursementMode = $mode, d.scholarshipId = $sid, d.accountNo = $acc "
                "WITH d "
                "MATCH (sc:Scholarship {scholarshipId: $sid}) "
                "MATCH (ba:BankAccount {accountNo: $acc}) "
                "MERGE (sc)-[:HAS_DISBURSEMENT]->(d) "
                "MERGE (d)-[:TO_ACCOUNT]->(ba)",
                {"did": ds[0], "sid": ds[1], "acc": ds[2], "ddate": ds[3], "amt": ds[4], "mode": ds[5]}
            )

        # 11. Fees & (Student)-[:HAS_FEE]->(Fee)
        for f in STUDENT_FEES:
            session.run(
                "MERGE (fee:Fee {feeId: $fid}) "
                "SET fee.name = $fid, fee.feeAmount = $amt, fee.dueDate = $due, fee.studentId = $sid "
                "WITH fee "
                "MATCH (st:Student {studentId: $sid}) "
                "MERGE (st)-[:HAS_FEE]->(fee)",
                {"fid": f[0], "sid": f[1], "amt": f[2], "due": f[3]}
            )

        # 12. Payments & (Fee)-[:HAS_PAYMENT]->(Payment)-[:PAID_VIA]->(PaymentMethod)
        for p in FEE_PAYMENTS:
            session.run(
                "MERGE (pay:Payment {paymentId: $pid}) "
                "SET pay.name = $pid, pay.amountPaid = $amt, pay.paymentDate = $pdate, pay.transactionId = $txn, pay.feeId = $fid, pay.methodId = $mid "
                "WITH pay "
                "MATCH (fee:Fee {feeId: $fid}) "
                "MATCH (pm:PaymentMethod {methodId: $mid}) "
                "MERGE (fee)-[:HAS_PAYMENT]->(pay) "
                "MERGE (pay)-[:PAID_VIA]->(pm)",
                {
                    "pid": p[0], "fid": p[1], "mid": p[3],
                    "pdate": p[4], "amt": p[5], "txn": p[6]
                }
            )
            if p[2]:  # If scholarship linked
                session.run(
                    "MATCH (pay:Payment {paymentId: $pid}) "
                    "MATCH (sc:Scholarship {scholarshipId: $sid}) "
                    "MERGE (pay)-[:USES_SCHOLARSHIP]->(sc)",
                    {"pid": p[0], "sid": p[2]}
                )

        print("✓ Neo4j graph database seeded successfully!")

        print("\nNeo4j Entity Counts Summary:")
        node_res = list(session.run("MATCH (n) RETURN labels(n)[0] as lbl, count(*) as cnt ORDER BY lbl"))
        for r in node_res:
            print(f"  {r['lbl']:20}: {r['cnt']:4} nodes")

        rel_res = list(session.run("MATCH ()-[r]->() RETURN type(r) as t, count(*) as cnt ORDER BY t"))
        print("\nNeo4j Relationship Counts Summary:")
        for r in rel_res:
            print(f"  {r['t']:20}: {r['cnt']:4} edges")


def main():
    parser = argparse.ArgumentParser(description="Seed demo dataset for Scholarship & Fee Management System.")
    parser.add_argument("--oracle", action="store_true", help="Seed Oracle database only")
    parser.add_argument("--neo4j", action="store_true", help="Seed Neo4j database only")
    parser.add_argument("--all", action="store_true", help="Seed both Oracle and Neo4j databases (default)")

    args = parser.parse_args()

    seed_all = args.all or (not args.oracle and not args.neo4j)

    if args.oracle or seed_all:
        seed_oracle()

    if args.neo4j or seed_all:
        seed_neo4j()

    print("\n✅ Seeding process completed successfully!")


if __name__ == "__main__":
    main()
