# Phase 0 Mandatory Project Audit Report
## Scholarship & Fee Management System — Unified Oracle SQL/PLSQL + Neo4j Graph Platform

**Date:** 23 October 2026  
**Auditor:** Senior UI/UX Designer, Frontend Architect, and QA Engineer  
**Branch:** `feature/da3-neo4j-backend` (Git HEAD: `f24eb6c`)  
**Repository Location:** `/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System`  

---

## 1. Executive Summary & Verification of Baseline

An exhaustive pre-implementation audit was conducted across the active codebase:
- **Test Suite Health:** All **168 automated tests** across 8 test suites pass in 3.33 seconds (`pytest`).
- **Database Services:** 
  - `scholarship-neo4j` container is **Up and healthy** on ports 7474 (HTTP) and 7687 (Bolt).
  - `oracle-free` container was started and verified running on port 1521 (`FREEPDB1`).
- **Backend Service:** Flask 3.1.3 serves **59 REST routes** (19 Oracle routes + 38 Neo4j blueprint routes + 2 static UI routes) without conflicts.
- **Frontend State:** Single Page Application at `index.html` (2,939 lines, 124 KB) using Vanilla JavaScript, Chart.js 4.4.1, and Cytoscape.js 3.28.1.

---

## 2. Directory Structure & Key Assets

```
/Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System/
├── index.html                      # Active frontend application (2,939 lines)
├── Dockerfile                      # Multi-stage production container build (python:3.12-slim)
├── docker-compose.yml              # Local multi-container orchestration (neo4j + backend)
├── Procfile / render.yaml          # PaaS deployment manifests
├── pytest.ini                      # Test runner configuration (testpaths = tests)
├── .gitignore                      # Git exclusion rules
├── backend/
│   ├── app.py                      # Flask WSGI app, 18 Oracle routes, static /app & /ui routes
│   ├── db.py                       # Oracle connection manager (oracledb 26.0.0)
│   ├── neo4j_db.py                 # Neo4j driver connection pool (@lru_cache)
│   ├── graph_service.py            # Graph business logic, Cypher execution (2,219 lines)
│   ├── neo4j_routes.py             # Neo4j Blueprint (/api/neo4j, 38 routes, 833 lines)
│   └── requirements.txt            # Flask, flask-cors, oracledb, neo4j, gunicorn
├── database/
│   ├── 01_create_tables.sql ... 06_plsql.sql  # Oracle schema, constraints, views, PL/SQL
│   └── neo4j/
│       ├── 01_constraints.cypher ... 06_query_verification.cypher  # Cypher scripts
├── tests/
│   ├── test_academic_routes.py     # 25 tests
│   ├── test_academic_service.py    # 29 tests
│   ├── test_app_integration.py     # 3 tests
│   ├── test_financial_routes.py    # 26 tests
│   ├── test_financial_service.py   # 26 tests
│   ├── test_graph_service.py       # 27 tests
│   ├── test_neo4j_live.py          # 4 tests (Live container integration)
│   └── test_neo4j_routes.py        # 28 tests
├── docs/                           # Architectural, test, and contract documentation
└── analysis_report/                # 13 comprehensive viva and architectural reports
```

---

## 3. Frontend Audit & Identified Problems

1. **Bug in Scholarship Awards by Category Chart:**
   - **Root Cause:** In `index.html`, `initCharts()` initializes `chartInstances.scholarship` with zeros (`[0, 0, 0]`). `loadScholarships()` fetches data from `/api/scholarships` and updates text count elements (`#meritCount`, etc.), but **never calls `updateCharts()`**. Furthermore, `updateCharts()` was omitted from the initial `Promise.all()` completion sequence. Consequently, the chart remains completely blank on page load.
2. **Conventional Horizontal Tab Navigation:**
   - The current UI uses flat top-level tab buttons (`.portal-nav`), which becomes crowded on smaller viewports and lacks the modern look of an enterprise dashboard.
   - It needs a **collapsible, modern left sidebar** with prominent icons, section groupings, and clear active states.
3. **Graph Explorer Visual Hierarchy & Inspector:**
   - The Cytoscape canvas is functional, but lacks a dark, modern high-contrast theme, relationship badges, and interactive relationship highlight/dimming.
   - Node click inspector is basic; it needs direct neighbor traversal, prominent label tags, and breadcrumbs.
   - Missing direct "View in Graph" deep-linking from student tables and scholarship records.
4. **Payment Workflow & Overpayment Feedback:**
   - The payment form requires manual calculation. It lacks a **live interactive payment preview card** that dynamically shows: *Total Assessed Fee*, *Already Paid*, *Current Outstanding*, *Proposed Payment*, and *Expected Remaining Balance* in real time.
5. **Visual Styling & Design System:**
   - Current CSS has fragmented color definitions and inconsistent spacing.
   - Needs a unified set of CSS custom properties (Design Tokens): Deep navy (`#0B132B`, `#0F172A`), cool slate (`#F8FAFC`, `#E2E8F0`), emerald/teal (`#10B981`, `#059669`), restrained blue (`#3B82F6`), refined shadows, and rounded card geometry (`12px`-`16px`).
   - Needs accessible Light/Dark theme switching.
6. **Toast Notifications & Modals:**
   - Status messages currently render in static inline containers. Needs an animated, floating toast notification system (Success, Error, Info) and accessible modal dialogs with backdrop blur.

---

## 4. API Dependencies & Preservation Plan

The redesign must strictly preserve all existing backend contracts:
- **Oracle Routes (`/api`):** 18 routes (`/students`, `/scholarships`, `/applications`, `/fees`, `/payments`, `/disbursements`, `/dashboard`).
- **Neo4j Routes (`/api/neo4j`):** 38 routes (`/health`, `/graph`, `/students`, `/fees`, `/payments`, `/scholarships`, `/disbursements`, `/bank-accounts`, etc.).
- **Engine Switcher:** The frontend's `switchEngine(engine)` function must continue updating `currentEngine` and dynamically prefixing API paths (`/api` vs `/api/neo4j`).
- **Zero Schema / Service Breaking Changes:** No database tables, columns, constraints, node labels, relationship types, or backend service signatures will be altered.

---

## 5. Proposed Phased Implementation Plan

- **Phase 1:** Establish Design System (CSS Custom Properties, Typography, Dark/Light Tokens, Elevation, Transitions).
- **Phase 2:** Build Modern Application Shell (Collapsible Left Sidebar with Iconography, Topbar with Live Engine Switcher & Health Indicator).
- **Phase 3:** Redesign Overview Dashboard (KPI Cards with Trend Badges, Fix Empty Category Chart, Enhanced Inflow/Outflow Charts).
- **Phase 4:** Upgrade Neo4j Graph Explorer (High-Contrast Theme, Interactive Node Inspector, Connected-Node Highlighting, Ego-Network Presets, Zoom/Fit Controls).
- **Phase 5:** Enhance Student Directory (Search, Sorting, Pagination/Limits, Student Detail Drawer, "View in Graph" Deep Link).
- **Phase 6:** Modernize Scholarship & Application Lifecycle (Status Badges, Approval/Rejection Dialogs, Category Drilldown).
- **Phase 7:** Redesign Fees & Payments (Live Interactive Payment Calculator, Dynamic Overpayment Warning, Transaction Reference).
- **Phase 8:** Upgrade Disbursements & Bank Accounts (Disbursement Limit Guard, Mode Badges, Banking Registry).
- **Phase 9:** Polish UX, Modals, Toasts, Responsive Layouts, and Accessibility.
- **Phase 10:** Verify Code Quality and Maintainability.
- **Phase 11:** Run Full Test Regression Suite (168 tests) & Browser Verification.
- **Phase 12:** Generate Final Deliverables and Documentation.
