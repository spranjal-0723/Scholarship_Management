# Production Cloud Deployment Guide
## Scholarship and Fee Management System — Render & Neo4j AuraDB Free

This guide provides step-by-step instructions for deploying the **Scholarship and Fee Management System** as a public, cloud-hosted website. Evaluators, faculty members, and peers can access and interact with the complete system from any laptop or mobile browser without installing Python, Docker, Oracle, or Neo4j locally.

---

## 1. Cloud Architecture Overview

```mermaid
flowchart TD
    User["Faculty / Evaluator Browser (Laptop or Mobile)"] -->|HTTPS / Port 443| Render["Render Web Service (Flask 3.1 + Gunicorn WSGI)"]
    
    subgraph RenderApp ["Render Cloud Hosting (Python 3.12)"]
        SPA["Single-Page Application (HTML5, Modern CSS, Vanilla JS)"]
        Gunicorn["Gunicorn WSGI (2 Workers, Timeout: 120s)"]
        FlaskBackend["Unified Flask REST API &amp; Session Auth"]
        ProxyFixMW["Werkzeug ProxyFix (Reverse Proxy Trust)"]
    end
    
    Render --> RenderApp
    Gunicorn --> FlaskBackend
    FlaskBackend --> ProxyFixMW
    
    subgraph CloudDatabase ["Neo4j AuraDB Free (Managed Cloud Graph)"]
        AuraCluster["Neo4j AuraDB Instance (neo4j+s://)"]
        CanonicalNodes["250 Canonical Graph Nodes"]
        CanonicalEdges["280 Directed Relationships"]
        Constraints["12 Schema Uniqueness Constraints"]
    end
    
    FlaskBackend -->|Encrypted TLS (neo4j+s://) / Keep-Alive| AuraCluster
    AuraCluster --> CanonicalNodes
    AuraCluster --> CanonicalEdges
    AuraCluster --> Constraints

    subgraph GitHubRepo ["GitHub Repository (Source of Truth)"]
        Code["Flask Backend + Frontend + Migration Tools"]
        OracleFiles["Oracle SQL / PLSQL Scripts (Preserved for DA-2 Viva)"]
    end
    
    GitHubRepo -->|Automatic Git Deploy on push| Render
```

### Academic Polyglot Persistence in Cloud Mode
- **Neo4j AuraDB Only (`APP_DATABASE_MODE=neo4j`):** The public cloud deployment operates directly against Neo4j AuraDB Free. Every table, KPI counter, search query, student detail dossier, fee invoice, payment receipt, and the interactive Cytoscape.js graph visualizer is dynamically powered by live Cypher graph traversals.
- **Oracle Codebase Preserved:** All Oracle DDL schemas, PL/SQL stored procedures, functions, database views, and financial triggers remain fully intact in `database/oracle/` for DA-2 academic evaluation. In cloud mode, the system gracefully marks Oracle as `"disabled_in_cloud_mode"` without crashing or degrading health.

---

## 2. Step 1: Provision Neo4j AuraDB Free Instance

Neo4j AuraDB Free is a fully managed, zero-maintenance cloud graph database with a permanent free tier.

1. **Sign Up or Log In:**
   - Go to [Neo4j Aura Console](https://console.neo4j.io/).
   - Sign in using your Google account or email.

2. **Create a Free Instance:**
   - Click **"New Instance"**.
   - Under **AuraDB**, select the **Free** tier (0.5 GB memory, 200k nodes, 400k relationships — plenty for our 250 nodes and 280 relationships).
   - Give the instance a name (e.g., `scholarship-management-graph`).
   - Choose a region geographically close to you (e.g., `us-east-1` or `eu-central-1`).

3. **Download Credentials File:**
   - AuraDB will generate a connection URI, username (`neo4j`), and a strong generated password.
   - **Crucial:** Click **"Download .env file"** or copy the credentials immediately. Neo4j does not show this password again.
   - Example credentials:
     ```env
     NEO4J_URI=neo4j+s://a1b2c3d4.databases.neo4j.io
     NEO4J_USERNAME=neo4j
     NEO4J_PASSWORD=your-generated-auradb-password
     AURA_INSTANCEID=a1b2c3d4
     AURA_INSTANCENAME=scholarship-management-graph
     ```

4. **Wait for Instance Status:**
   - The instance will change from `Creating` to `Running` in about 1–2 minutes.

---

## 3. Step 2: Migrate Canonical Benchmark Dataset to AuraDB

We provide an idempotent, robust migration script (`scripts/migrate_to_auradb.py`) that applies 12 schema constraints, creates all 250 nodes, connects all 280 relationships, and executes an automated parity audit.

### A. Test Connectivity with Dry Run (Safe)
Run the migration script with `--dry-run` to ensure your AuraDB instance is reachable:

```bash
cd /Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System

backend/venv/bin/python scripts/migrate_to_auradb.py \
  --uri "neo4j+s://<YOUR_INSTANCE_ID>.databases.neo4j.io" \
  --user neo4j \
  --password "<YOUR_AURADB_PASSWORD>" \
  --dry-run
```

Expected output:
```text
=================================================================
  SCHOLARSHIP MANAGEMENT — NEO4J AURADB (CLOUD) MIGRATION TOOL
=================================================================
Target URI     : neo4j+s://<YOUR_INSTANCE_ID>.databases.neo4j.io
Target User    : neo4j
Target Database: neo4j
Clear First    : NO (Safe Idempotent Merge)
Dry Run        : YES
=================================================================

[Step 1/5] Connecting to Neo4j instance...
✓ Connectivity verified successfully!

✓ Dry-run completed successfully! Database is reachable. Exiting.
```

### B. Run Complete Migration
Execute the full idempotent migration:

```bash
backend/venv/bin/python scripts/migrate_to_auradb.py \
  --uri "neo4j+s://<YOUR_INSTANCE_ID>.databases.neo4j.io" \
  --user neo4j \
  --password "<YOUR_AURADB_PASSWORD>"
```

*Note: If you are re-migrating a fresh or dirty instance and want a clean start, add `--clear-first`.*

### C. Verify Parity Audit Summary
The script will output the migration audit:

```text
=================================================================
                 MIGRATION AUDIT SUMMARY
=================================================================
Total Graph Nodes        : 250 (Expected: 250)
Total Graph Relationships: 280 (Expected: 280)
Node Labels (12 Target)  : 12 found
Relationship Types (12)  : 12 found
=================================================================
🎉 100% PARITY CONFIRMED! All canonical nodes and relationships are active.
```

---

## 4. Step 3: Deploy Web Service to Render

Render offers free cloud web service hosting with automatic GitHub integration.

### Method A: Connect Web Service via Render Dashboard (Recommended)

1. Log in to [dashboard.render.com](https://dashboard.render.com/).
2. Click **"New +"** and select **"Web Service"**.
3. Choose **"Build and deploy from a Git repository"** and select or paste your repository:
   `https://github.com/spranjal-0723/Scholarship_Management`
4. Configure the service parameters:
   - **Name:** `scholarship-fee-management` (or any preferred name)
   - **Region:** Any (e.g., Oregon or Frankfurt)
   - **Branch:** `main`
   - **Root Directory:** *(leave blank)*
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn "backend.app:app" --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Instance Type:** `Free`
5. Expand **"Advanced"**:
   - **Health Check Path:** `/healthz`
   - **Auto-Deploy:** `Yes`
6. Under **Environment Variables**, add the following keys:

| Key | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.12.0` | Python runtime version |
| `APP_ENV` | `production` | Production environment flag |
| `APP_DATABASE_MODE` | `neo4j` | Locks backend routing to Neo4j AuraDB |
| `FLASK_DEBUG` | `false` | Disables debug mode in production |
| `DEMO_READ_ONLY` | `false` | Set `true` if you wish to block write operations |
| `FLASK_SECRET_KEY` | *(A long random secret string)* | Used for cryptographic session signing |
| `NEO4J_URI` | `neo4j+s://<YOUR_INSTANCE_ID>.databases.neo4j.io` | Your AuraDB connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `<YOUR_AURADB_PASSWORD>` | Neo4j AuraDB password |
| `NEO4J_DATABASE` | `neo4j` | AuraDB default database name |
| `CORS_ALLOWED_ORIGINS` | `*` | Permits cross-origin requests |
| `DEMO_ADMIN_EMAIL` | `admin@scholarship.demo` | Demo admin login email |
| `DEMO_ADMIN_PASSWORD` | `Demo@12345` | Demo admin login password |

7. Click **"Create Web Service"**.
8. Render will clone the repository, install dependencies, run health checks on `/healthz`, and assign a public URL (e.g., `https://scholarship-fee-management.onrender.com`).

---

### Method B: Deploy via Render Blueprint (`render.yaml`)

Because this repository includes a pre-configured `render.yaml` specification, you can also deploy using Render Blueprints:

1. In Render dashboard, click **"New +"** -> **"Blueprint"**.
2. Select your repository `spranjal-0723/Scholarship_Management`.
3. Render will parse `render.yaml` automatically and prompt only for the secret environment variables (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`).
4. Click **"Apply"**.

---

## 5. Step 4: Verification & Evaluator Testing Checklist

Once your Render deployment is live, verify the installation using this checklist:

### 1. Health Probe
Open `https://<YOUR-RENDER-URL>/healthz` in your browser:
```json
{
  "mode": "neo4j",
  "service": "scholarship-fee-management",
  "status": "live"
}
```

### 2. Configuration Inspection
Open `https://<YOUR-RENDER-URL>/api/config`:
```json
{
  "app_name": "Scholarship and Fee Management System",
  "database_mode": "neo4j",
  "environment": "production",
  "neo4j_enabled": true,
  "oracle_enabled": false,
  "read_only": false
}
```

### 3. Application UI & Login
1. Navigate to `https://<YOUR-RENDER-URL>/` (or `/app`).
2. The modern Navy & Teal login portal will appear.
3. Click the **"Fill Demo Admin"** pill or manually type:
   - **Email:** `admin@scholarship.demo` (or `faculty@scholarship.demo`)
   - **Password:** `Demo@12345`
4. Click **"Sign In"**. You are granted an authenticated session with an encrypted `HttpOnly` session cookie.

### 4. Interactive Dashboard Verification
- **KPI Cards:** Verify Students (25), Scholarships (15), Applications (35), Fees (30), Payments (32), Disbursements (18) display correct benchmark numbers.
- **Analytics Charts:** Verify Chart.js renders the scholarship distribution donut and fee collection bar chart.
- **Engine Badge:** Notice the engine badge in the header shows:
  `Active Engine: Neo4j AuraDB Cloud Database (/api/neo4j)`
- **Oracle Pill:** Hovering over the `Oracle (Local)` engine button informs the evaluator that Oracle is active in local Docker mode, while cloud mode is powered by Neo4j AuraDB.

### 5. Interactive Cytoscape.js Graph Explorer
1. Click the **"Graph Explorer"** tab in the sidebar navigation.
2. Verify that Cytoscape.js dynamically loads all canonical nodes and relationships from AuraDB.
3. Test layout algorithms (**Cose**, **Breadthfirst**, **Concentric**, **Circle**).
4. Search for a student (e.g., `S001` or `Arjun Sharma`) to focus and highlight connected graph neighbors.
5. Click any node to open the interactive entity metadata inspector.

---

## 6. Troubleshooting & Operational Advice

### Render Free Tier Cold Starts
- Render free-tier services spin down after 15 minutes of inactivity.
- When an evaluator first opens the URL after an idle period, Render takes approximately **30–50 seconds** to wake up the container.
- *Recommendation for Viva:* Open the website 2–3 minutes before presenting so the container is already warm and responds instantaneously.

### Neo4j AuraDB Free Inactivity Pausing
- Free AuraDB instances may automatically pause after 3 days of complete inactivity.
- If this occurs, simply log into [console.neo4j.io](https://console.neo4j.io/) and click the **"Resume"** button. The database restores within 60 seconds without data loss.

### Read-Only Protection for Public Demos
- If you share your website publicly and want to prevent external visitors from altering test data or submitting dummy applications, set:
  ```env
  DEMO_READ_ONLY=true
  ```
  in the Render Environment Variables tab.
- All `POST`, `PUT`, and `DELETE` requests will return an explanatory HTTP 403 message while preserving full read, traversal, and graph exploration capabilities.

---

## 7. Local vs. Cloud Architecture Comparison

| Feature | Local Full-Stack Evaluation | Render + Neo4j AuraDB Cloud |
|---|---|---|
| **Target Audience** | Academic viva, terminal inspection, unit tests | Direct evaluator browser review, mobile access |
| **Relational Database** | Oracle Database 23ai Free (Docker on port 1521) | Preserved in Git repository (`database/oracle/`) |
| **Graph Database** | Neo4j Community 5.26 (Docker on port 7687) | Neo4j AuraDB Free (`neo4j+s://...`) |
| **Engine Switching** | Real-time dual-engine toggle (`Oracle` <-> `Neo4j`) | Locked to `Neo4j AuraDB Cloud` |
| **Web Server** | Flask Development Server (`PORT=5050`) | Production Gunicorn WSGI (`2 workers`, `120s timeout`) |
| **Prerequisites** | Docker Desktop, Python 3.11+, 8GB RAM | Zero prerequisites (Any modern web browser) |
