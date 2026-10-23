# Complete Codebase Analysis & Viva Preparation
# Deliverable 06: Frontend Walkthrough

**Project Title:** Scholarship and Fee Management System  
**Frontend Technology:** Single-Page Application (HTML5, Modern CSS3, Vanilla ES6+ JavaScript)  
**External Visual Libraries:** Cytoscape.js 3.28.1 (Graph Explorer), Chart.js (Responsive Analytics)  
**Audited Files:**  
1. `ScholarshipManagementDA2-main/index.html` (627 lines: Offline DA-2 Prototype)  
2. `Scholarship-and-Fee-Management-System/index.html` (2,939 lines: Full DA-3 Enterprise Portal)  
**Evidence Level:** `[VERIFIED]` directly from DOM structures, styles, and JavaScript event bindings.

---

## 1. Evolution: The Two Frontend Implementations

A key insight for your DBMS Viva is understanding why two versions of `index.html` exist across the folders:

```
[DA-2 Archive: index.html (627 Lines)]
  - Offline Standalone Prototype
  - Data stored in browser window.localStorage ("sfms.fixed.students.v1", "sfms.fixed.fees.v1")
  - Explicit warning banner: "Changes are saved in this browser... works without starting a local backend"
  - No network fetch() calls
  - No Cytoscape.js graph canvas
  - Built by Member 1 for early visual demonstration
         |
         v (Evolved and Integrated in DA-3)
[DA-3 Active Workspace: index.html (2,939 Lines)]
  - Full-Stack Dual-Engine Enterprise Portal
  - Zero localStorage dependencies for operational records
  - Live asynchronous window.fetch() calls to Flask endpoints (/api and /api/neo4j)
  - Illustrated Vector Campus Entrance Scene with animated student silhouettes
  - Cytoscape.js Interactive Graph Canvas (5 layouts, node inspector, ego-network filtering)
  - Chart.js Financial Reconciliation and Scholarship Allocation Charts
  - Dynamic Dual-Engine Switcher (Active Database: Oracle vs Neo4j)
```

---

## 2. User Journey & Campus Entrance Experience

### A. The Campus Gate Entrance Screen (`#introScreen`)
When the user visits `http://127.0.0.1:5000/app` (or opens `index.html`), they are greeted by an illustrated classical campus scene:
- **Visual Design:** Pure SVG/CSS rendering of a collegiate classical facade featuring ionic columns, an engraved pediment crest (`S` for Scholaris), glowing window panes, a clocktower, a cobblestone pathway, and volumetric lampposts.
- **Dynamic Animation:** Vector student silhouettes walk along the cobblestone quad toward the central portal via CSS keyframe animations (`@keyframes walkAlongPath`).
- **Interaction:**
  - Clicking **"Enter Dashboard ↗"** or pressing **Escape** triggers a smooth camera zoom transition (`.intro-screen.is-leaving`), fading out the gate overlay and scrolling to the main workspace.
  - Reduced-motion accessibility is fully supported via `@media (prefers-reduced-motion: reduce)`.
  - A persistent **"🏛️ Campus Gate"** button in the navigation header allows evaluators to re-trigger the entrance animation at any time.

---

## 3. Navigation & Dual-Engine Database Switcher

### A. Sidebar Navigation (`.sidebar`)
The left sidebar provides instant navigation across functional workspaces:
1. **Overview (`data-target="overview"`):** Summary metrics and financial charts.
2. **Students (`data-target="students"`):** Complete student directory, enrollment, and search.
3. **Fee Records (`data-target="fees"`):** Fee invoice ledger, payment recorder, and balance calculator.
4. **Scholarships (`data-target="scholarships"`):** Scholarship opportunities and recipient breakdown.
5. **Neo4j Graph Explorer (`data-target="graph"`):** Interactive Cytoscape.js topological graph.

### B. Dynamic Dual-Engine Switcher (`#engineSelector`)
Located prominently in the top application bar, the engine selector enables instant database switching:
- **UI Control:** Dropdown / Pill `<select id="engineSelector">` with options:
  - `Oracle Database (/api)`: Routes all requests to Oracle SQL endpoints.
  - `Neo4j Graph Database (/api/neo4j)`: Routes all requests to Neo4j Cypher endpoints.
- **JavaScript Mechanism (`switchEngine(engine)`):**
  ```javascript
  function switchEngine(engine) {
      currentEngine = engine;
      const badge = document.getElementById("engineBadge");
      if (engine === "neo4j") {
          badge.textContent = "Active Database: Neo4j Graph Database (/api/neo4j)";
          badge.className = "engine-badge neo4j-active";
      } else {
          badge.textContent = "Active Database: Oracle Database Free (/api)";
          badge.className = "engine-badge oracle-active";
      }
      refreshActiveView(); // Reloads tables from newly selected database
  }
  ```
- **Fetch Wrapper (`fetchAPI(endpoint, options)`):**
  Automatically rewrites URLs: if `currentEngine === 'neo4j'`, `/api/students` becomes `/api/neo4j/students`.

---

## 4. Workspaces and Interactive Components

### A. Executive Dashboard & Visual Analytics (Chart.js)
1. **Four Summary Metric Cards (`.dashboard`):**
   - **Total Students:** Count of enrolled students.
   - **Scholarship Students:** Count of students holding approved scholarships.
   - **Total Fee Assessed:** Cumulative tuition billed in INR (`money.format()`).
   - **Pending Payments / Outstanding:** Net outstanding student fee balance.
2. **Chart.js Financial Visualizations:**
   - **Fee Reconciliation Chart:** Responsive Bar Chart comparing *Total Assessed Fee* vs *Collected Revenue* vs *Outstanding Dues*.
   - **Scholarship Lifecycle Doughnut Chart:** Breakdown of applications by status (`Approved`, `Pending`, `Rejected`).
   - **Scholarship Award Categories:** Bar chart illustrating disbursements across Merit, Need-Based, and Sports categories.

### B. Student Directory Workspace (`#studentRecordsSection`)
- **Live Search Toolbar (`#searchStudent`):** Real-time client-side substring filtering across Student ID and Student Name on the `input` event.
- **Student Data Table (`#studentTableBody`):** Displays Student ID, Name, Phone, Degree Program, Department, and assigned Scholarship.
- **Add Student Modal / Form (`#studentForm`):**
  - Inputs: Student ID, Name, Phone Number, Program Dropdown, Address fields.
  - Client Validation: Enforces phone pattern `^[+0-9() -]{7,15}$`, non-empty ID, and program selection.
  - Submits via `POST /api/students` or `POST /api/neo4j/students`.
- **Inline Row Editing (`saveStudentEdit(id)`):**
  - Clicking "Edit" replaces row text with inline `<input>` and `<select>` controls.
  - "Save" sends update payload; "Cancel" restores original row without page reload.

### C. Tuition Fee Ledger Workspace (`#feeManagementSection`)
- **Fee Ledger Table (`#feeTableBody`):**
  - Displays Fee ID, Student ID, Assessed Tuition Fee (₹), Paid Fee (₹), Outstanding Balance (₹), and Status Badge (`.status.paid` [Green] vs `.status.pending` [Amber]).
- **Add Fee Invoice Form (`#feeForm`):**
  - Inputs: Student ID, Fee Amount (₹), Due Date (`YYYY-MM-DD`).
  - Validation: Amount must be $> 0$; Student ID must exist.
  - Submits via `POST /api/fees`.
- **Record Fee Payment Form:**
  - Inputs: Fee ID, Amount to Pay (₹), Payment Method (UPI, Net Banking, Credit Card, Debit Card), Transaction ID.
  - **Client Overpayment Guard:** Validates that `paidFee + amountPaid <= totalFee` before submitting.
  - Submits via `POST /api/payments`.

### D. Scholarship Funding Workspace (`#scholarshipManagementSection`)
- **Scholarship Catalog:** Displays available grant categories, eligibility criteria, and maximum award limits.
- **Application Submission:** Allows students to apply for financial aid.
- **Approval Workflow:** Administrators review pending applications and toggle status to `Approved` or `Rejected` via `PUT /api/applications/<id>/status`.

---

## 5. Cytoscape.js Interactive Neo4j Graph Explorer

The centerpiece of the DA-3 frontend is the **Neo4j Graph Explorer** (`#cy`), rendered on an HTML5 canvas powered by **Cytoscape.js 3.28.1**.

```
+----------------------------------------------------------------------------------------------------+
|                                    CYTOSCAPE GRAPH EXPLORER CANVAS                                 |
|                                                                                                    |
|  [Toolbar: Layout (COSE/Concentric) | Presets | Entity Filter: Student/Fee | Search: [     ] ]     |
|                                                                                                    |
|            (:Department {D01})                                                                     |
|                    |                                                                               |
|             [:HAS_PROGRAM]                                                                         |
|                    v                                                                               |
|            (:Program {P01})                                                                        |
|                    |                                                                               |
|             [:HAS_STUDENT]                                                                         |
|                    v                                                                               |
|            (:Student {S001}) --------[:SUBMITTED]-------> (:Application {APP001})                  |
|              /           \                                        |                                |
|        [:HAS_FEE]    [:HAS_PROFILE]                           [:AWARDS]                            |
|            /               \                                      v                                |
|           v                 v                            (:Scholarship {SCH001})                   |
|     (:Fee {F001})    (:StudentProfile)                            |                                |
|           |                                              [:HAS_DISBURSEMENT]                       |
|     [:HAS_PAYMENT]                                                v                                |
|           v                                              (:Disbursement {DIS001})                  |
|    (:Payment {PAY001})                                            |                                |
|           |                                                  [:TO_ACCOUNT]                         |
|      [:PAID_VIA]                                                  v                                |
|           v                                              (:BankAccount {AC001})                    |
|  (:PaymentMethod {M01})                                                                            |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

### A. Graph Styling & Color Taxonomy
Every node label has a distinctive color, geometric shape, and font weight defined in the Cytoscape stylesheet:
- **`:Student`:** Royal Blue (`#3b82f6`), Circle / Ellipse.
- **`:Department`:** Purple (`#8b5cf6`), Rounded Rectangle.
- **`:Program`:** Indigo (`#6366f1`), Octagon.
- **`:Scholarship`:** Gold (`#d97706`), Star.
- **`:Application`:** Orange (`#f97316`), Diamond.
- **`:Fee`:** Crimson Red (`#ef4444`), Rectangle.
- **`:Payment`:** Emerald Teal (`#10b981`), Vee / Triangle.
- **`:PaymentMethod`:** Light Cyan (`#06b6d4`), Hexagon.
- **`:BankAccount`:** Slate Grey (`#64748b`), Barrel.
- **Directed Edges:** Bezier curves with arrows (`mid-target-arrow: triangle`), labeled with relationship types (`HAS_STUDENT`, `AWARDS`, `HAS_PAYMENT`, etc.).

### B. Five Dynamic Physics Layouts
Users can dynamically recalculate the graph topology using the layout dropdown:
1. **COSE (Compound Spring Embedder):** Force-directed physics simulation where nodes repel and edges act as elastic springs.
2. **Concentric:** Radial layout placing high-degree central nodes (e.g. university departments) in the center, radiating outward to students.
3. **Breadthfirst:** Hierarchical Directed Acyclic Graph (DAG) visualizing top-down academic lineage (Department $\rightarrow$ Program $\rightarrow$ Student).
4. **Circle:** Distributes all nodes along a single mathematical perimeter.
5. **Grid:** Aligns nodes in regular geometric rows and columns.

### C. Quick Analytical Presets
- **"Complete Graph":** Resets filters and displays all 54 nodes and 55 relationships.
- **"Aarav Sharma (S001) Ego Network":** Passes `?student_id=S001` to isolate all records within 3 relationship hops of S001.
- **"Fee & Payment Flow":** Filters nodes by `:Fee`, `:Payment`, and `:PaymentMethod`.
- **"Scholarship Pipeline":** Filters nodes by `:Application`, `:Scholarship`, `:Disbursement`, and `:BankAccount`.

### D. Interactive Node Inspector (`#nodeInspectorPanel`)
Clicking any node on the Cytoscape canvas pauses physics and opens a detailed side panel:
- **Node Title & Primary Key:** Displays label and canonical ID.
- **Property Table:** Key-value breakdown of all stored properties.
- **Incoming Edges:** Clickable list of source nodes pointing to this entity.
- **Outgoing Edges:** Clickable list of target nodes this entity points to.
- Clicking any connected neighbor instantly centers and zooms the canvas to that neighbor.

---

## 6. Complete UI Control to Backend API Mapping

| UI Action / Control | Frontend Event & Function | HTTP Request | Backend Endpoint | Database Action Executed |
| :--- | :--- | :--- | :--- | :--- |
| **Enter Portal** | Click `#enterDashboardBtn` | None (DOM Animation) | Static route `/app` | Reveals main application view |
| **Switch Database** | Change `#engineSelector` | `switchEngine(engine)` | Toggles base URL prefix | Routes future calls to `/api` or `/api/neo4j` |
| **Search Students** | Input `#searchStudent` | `renderStudents()` | Client-side filter | Substring match on loaded records |
| **Add Student Submit**| Submit `#studentForm` | `addStudent()` | `POST /api/students` | Inserts `STUDENT` row or `:Student` node |
| **Filter Graph by Ego**| Click "S001 Ego Network"| `loadGraphPreset('S001')` | `GET /api/neo4j/graph?student_id=S001` | Multi-hop Cypher traversal `[*1..3]` |
| **Create Fee Invoice**| Submit `#feeForm` | `addFeeRecord()` | `POST /api/fees` | Inserts `STUDENT_FEE` row or `:Fee` node |
| **Record Payment** | Submit `#paymentForm` | `addPaymentRecord()` | `POST /api/payments` | Executes payment insert with overpayment check |
| **Approve Application**| Click "Approve" button | `updateAppStatus(id, 'Approved')` | `PUT /api/applications/<id>/status` | Updates status to `'Approved'` |
| **Change Graph Layout**| Select `#graphLayoutSelect`| `cyInstance.layout(...).run()` | None (Browser Canvas) | Runs physics layout simulation |
| **Click Graph Node** | Tap on Cytoscape node | `cy.on('tap', 'node', handler)` | `GET /api/neo4j/nodes/<label>/<id>` | Opens Node Inspector side drawer |
