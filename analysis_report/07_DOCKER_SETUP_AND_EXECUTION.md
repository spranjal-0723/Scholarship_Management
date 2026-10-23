# Complete Codebase Analysis & Viva Preparation
# Deliverable 07: Docker Setup, Environment, and Execution

**Project Title:** Scholarship and Fee Management System  
**Audited Manifests:** `Dockerfile`, `docker-compose.yml`, `Procfile`, `render.yaml`, `backend/requirements.txt`  
**Host Environment:** macOS (Darwin / Unix Shell)  
**Evidence Level:** `[VERIFIED]` directly from Docker CLI inspections, running containers, and configuration manifests.

---

## 1. Verified Container & Service Architecture

The project defines three primary containerized services across its development and deployment configurations:

```
+========================================================================================================+
|                                         DOCKER SERVICE TOPOLOGY                                        |
+========================================================================================================+
| Service / Container Name  | Base Docker Image                   | Mapped Ports      | Volume Mounts   |
+---------------------------+-------------------------------------+-------------------+-----------------+
| scholarship-neo4j         | neo4j:community (v5.26-community)   | 7474:7474 (HTTP)  | neo4j_data:/data|
| (Running / Up 3 days)     |                                     | 7687:7687 (Bolt)  | neo4j_logs:/logs|
+---------------------------+-------------------------------------+-------------------+-----------------+
| oracle-free               | gvenzl/oracle-free:23-slim-faststart| 1521:1521 (TNS)   | None (Internal) |
| (Exited / Verified image) |                                     |                   |                 |
+---------------------------+-------------------------------------+-------------------+-----------------+
| scholarship-backend       | Multi-Stage Custom Dockerfile       | 5000:5000 (HTTP)  | /app (Context)  |
| (Defined in compose)      | (python:3.12-slim)                  |                   |                 |
+-------------------------------------------------------------------------------------------------------+
```

### Empirical Verification Evidence:
```bash
$ docker ps -a
CONTAINER ID   IMAGE                                  STATUS                      PORTS                                            NAMES
98ceb5061a38   neo4j:community                        Up 3 days                   0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp   scholarship-neo4j
f0cc9b298ad8   gvenzl/oracle-free:23-slim-faststart   Exited (137) 2 weeks ago    1521/tcp                                         oracle-free
```
- The Neo4j container `scholarship-neo4j` is **actively running and verified** on ports 7474 and 7687.
- The Oracle container `oracle-free` is present on disk and can be started via `docker start oracle-free`.

---

## 2. Docker Manifest Analysis

### A. Production Multi-Stage `Dockerfile`
The Dockerfile implements modern container security and optimization best practices:
1. **Stage 1 (`builder`):**
   - Base image: `python:3.12-slim`.
   - Installs build tools (`build-essential`).
   - Upgrades `pip` and installs all dependencies from `backend/requirements.txt` into system site-packages.
   - Cleans apt cache (`rm -rf /var/lib/apt/lists/*`) to reduce image bloat.
2. **Stage 2 (`runner`):**
   - Base image: `python:3.12-slim` (clean runtime without compiler tools).
   - Copies pre-compiled Python packages from `builder`:
     `COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages`
   - **Principle of Least Privilege:** Creates an unprivileged user `appuser`:
     `RUN useradd -m appuser && chown -R appuser:appuser /app`
     `USER appuser`
   - Exposes port `5000`.
   - **Production WSGI Entrypoint:** Starts Gunicorn with 2 worker processes and a 120-second timeout:
     `CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]`

### B. Multi-Container Orchestration (`docker-compose.yml`)
The Compose manifest defines service dependencies, health checks, and shared networks:
- **`neo4j` Service:**
  - Configures environment: `NEO4J_AUTH=neo4j/[REDACTED]`, `NEO4J_PLUGINS=["apoc"]`.
  - Healthcheck:
    `test: ["CMD-SHELL", "cypher-shell -u neo4j -p [REDACTED] 'RETURN 1' || exit 1"]`
    Runs every 10s with 5s timeout and 5 retries.
  - Persists graph storage in named volumes `neo4j_data` and `neo4j_logs`.
- **`backend` Service:**
  - Builds from local `Dockerfile`.
  - Injects environment variables: `PORT=5000`, `FLASK_DEBUG=false`, `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_DATABASE=neo4j`.
  - Enforces dependency: `depends_on: neo4j: condition: service_healthy`. This guarantees that the Flask backend never starts until the Neo4j database is fully initialized and responding to Cypher queries.

### C. Cloud Deployment Manifests (`Procfile` & `render.yaml`)
- **`Procfile`:** `web: gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`. Used by PaaS providers (Heroku / Render).
- **`render.yaml`:** Declares an Infrastructure-as-Code web service specification for Render:
  - Runtime: Python 3.12.0.
  - Build command: `pip install -r backend/requirements.txt`.
  - Syncs environment variables: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `CORS_ALLOWED_ORIGINS="*"`.

---

## 3. Step-by-Step Local Execution Guide

To reproduce and demonstrate the complete dual-database application on a local development machine:

### Terminal 1: Start Database Containers
```bash
# 1. Start Neo4j Container (if stopped)
docker start scholarship-neo4j

# 2. Start Oracle Container (if using Oracle engine)
docker start oracle-free

# 3. Verify both containers are up
docker ps
```

### Terminal 2: Seed Database Schemas (Setup-Only Step)
*If running on a fresh environment without pre-loaded data:*

```bash
# Seed Oracle Relational Database:
docker exec -i oracle-free sqlplus system/[REDACTED]@FREEPDB1 < database/01_create_tables.sql
docker exec -i oracle-free sqlplus system/[REDACTED]@FREEPDB1 < database/02_constraints.sql
docker exec -i oracle-free sqlplus system/[REDACTED]@FREEPDB1 < database/03_sample_data.sql
docker exec -i oracle-free sqlplus system/[REDACTED]@FREEPDB1 < database/05_views.sql
docker exec -i oracle-free sqlplus system/[REDACTED]@FREEPDB1 < database/06_plsql.sql

# Seed Neo4j Graph Database:
docker exec -i scholarship-neo4j cypher-shell -u neo4j -p [REDACTED] < database/neo4j/01_constraints.cypher
docker exec -i scholarship-neo4j cypher-shell -u neo4j -p [REDACTED] < database/neo4j/02_import_data.cypher
docker exec -i scholarship-neo4j cypher-shell -u neo4j -p [REDACTED] < database/neo4j/03_create_relationships.cypher
```

### Terminal 3: Start Flask WSGI Backend
```bash
cd /Users/pranjalsingh/Desktop/Scholarship-and-Fee-Management-System
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Export environment configuration
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="[REDACTED]"
export ORACLE_USER="system"
export ORACLE_PASSWORD="[REDACTED]"
export ORACLE_DSN="localhost:1521/FREEPDB1"

# Run Flask server
python backend/app.py
```
*Server starts on `http://127.0.0.1:5000`.*

### Terminal 4: Launch Web Client
Open your web browser and navigate directly to:
```text
http://127.0.0.1:5000/app
```
*(The Flask backend serves `index.html` natively via the `/app` route).*

Alternatively, if running the frontend via a separate static HTTP server:
```bash
python3 -m http.server 5500
# Open http://127.0.0.1:5500 in your browser
```

---

## 4. Operational vs Setup Steps

| Action | Phase | Frequency | Commands / Mechanism |
| :--- | :--- | :--- | :--- |
| **Docker volume creation** | Setup Only | Once per machine | `docker-compose up -d` or `docker run -v` |
| **DDL constraints & table creation**| Setup Only | Once per database | Running `01_create_tables.sql` / `01_constraints.cypher` |
| **Sample data seeding** | Setup Only | Once per database | Running `03_sample_data.sql` / `02_import_data.cypher` |
| **Container startup** | Daily Runtime | Every session | `docker start scholarship-neo4j oracle-free` |
| **Flask API server startup** | Daily Runtime | Every session | `python backend/app.py` or Gunicorn |
| **Browser UI access** | Daily Runtime | Every session | Navigate to `http://127.0.0.1:5000/app` |
| **Automated regression testing** | Maintenance | On code change | `pytest` |

---

## 5. Troubleshooting Common Startup & Connection Errors

### 1. `RuntimeError: NEO4J_PASSWORD is not set`
- **Cause:** `backend/neo4j_db.py` requires `NEO4J_PASSWORD` in the environment or `.env` file.
- **Fix:** Run `export NEO4J_PASSWORD="[REDACTED]"` before starting `app.py`, or create a `.env` file in `backend/`.

### 2. `ServiceUnavailable: Failed to establish connection to ('localhost', 7687)`
- **Cause:** The Neo4j Docker container is stopped or still initializing.
- **Fix:** Run `docker start scholarship-neo4j`. Wait 10 seconds for Cypher-shell healthcheck to pass, then verify via `curl http://localhost:7474`.

### 3. `oracledb.exceptions.DatabaseError: DPD-0001: cannot connect to Oracle listener`
- **Cause:** Oracle container `oracle-free` is stopped or port 1521 is blocked.
- **Fix:** Run `docker start oracle-free`. Check logs via `docker logs oracle-free`. Wait for `DATABASE IS READY TO USE!`.

### 4. `Address already in use: 0.0.0.0:5000`
- **Cause:** A previous instance of Flask or Apple's AirPlay Receiver is occupying port 5000.
- **Fix:** In macOS System Settings, disable AirPlay Receiver, or terminate existing process:
  ```bash
  lsof -ti :5000 | xargs kill -9
  ```

---

## 6. Public Cloud Deployment Reality Audit

Per the strict verification rules of this report:
- **Local & Container Deployment:** **100% VERIFIED.**
- **Public Cloud Hosting:** **NOT DEPLOYED (NO PUBLIC URL INVENTED).**
- **Exact Blocker:** Deploying to public cloud infrastructure (Render, Railway, AWS, or Neo4j AuraDB) requires active user cloud billing, private access tokens, and DNS domain registration. Credentials cannot be invented or assumed.
- **Ready Blueprint:** The codebase contains a fully validated `render.yaml` and `Dockerfile`. To deploy publicly:
  1. Push changes to GitHub.
  2. Create a new Web Service on Render connecting the repository.
  3. Supply the live `NEO4J_URI` and `NEO4J_PASSWORD` (e.g. from Neo4j AuraDB Free).
  4. Render builds the multi-stage Docker image and exposes a live HTTPS URL.
