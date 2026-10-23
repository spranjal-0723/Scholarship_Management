# DA-3 Deployment & Production Operations Guide

**Project:** Scholarship and Fee Management System  
**Date:** 22 October 2026  
**Architecture:** Flask 3.1 + Gunicorn WSGI + Neo4j 5.26 Property Graph  

---

## 1. Production Architecture Overview

The system runs as a hybrid multi-model DBMS web application:
- **Application Server:** Python 3.12/3.14 Flask backend served via Gunicorn WSGI.
- **Graph Database Engine (DA-3):** Neo4j 5+ (via Bolt driver protocol on port 7687).
- **Relational Database Engine (DA-2):** Oracle Database (accessible via `oracledb` thin client).
- **Frontend Presentation:** HTML5/CSS3 Single-Page Interface served statically or from Flask at `/app` or `/ui`.

---

## 2. Environment Configuration

### Required Environment Variables
Set these variables in your production environment (e.g., Render Dashboard, Railway Variables, or Docker `.env`):

| Variable | Description | Example / Default | Production Recommendation |
|---|---|---|---|
| `FLASK_DEBUG` | Flask debug mode | `false` | **MUST BE `false`** |
| `PORT` | Listening web port | `5000` | Injected by cloud platform |
| `HOST` | Bind address | `0.0.0.0` | `0.0.0.0` |
| `NEO4J_URI` | Neo4j Bolt connection URI | `bolt://localhost:7687` | `neo4j+s://<dbid>.databases.neo4j.io` (AuraDB) or `bolt://neo4j:7687` (Docker) |
| `NEO4J_USER` | Neo4j username | `neo4j` | Least-privilege user |
| `NEO4J_PASSWORD` | Neo4j password | `scholarship123` | Strong secret |
| `NEO4J_DATABASE` | Target database name | `neo4j` | `neo4j` |
| `CORS_ALLOWED_ORIGINS` | Permitted frontend origins | `*` (dev) | Specific production domain, e.g. `https://my-app.onrender.com` |
| `ORACLE_USER` | Oracle username (DA-2) | `c##spranjal` | Optional in Neo4j-only mode |
| `ORACLE_PASSWORD` | Oracle password (DA-2) | - | Secret |
| `ORACLE_DSN` | Oracle Host/Service | `localhost:1521/XE` | - |

> [!WARNING]
> Never commit `.env` or production credentials to Git. Add `.env` to `.gitignore`.

---

## 3. Deployment Options

### Option A: 1-Click Cloud Deployment via Render (Recommended)
This repository includes a native `render.yaml` blueprint.

1. Connect your GitHub repository to [Render.com](https://render.com).
2. Choose **New > Blueprint** and select `render.yaml`.
3. In the Render Dashboard under **Environment**:
   - Provide your cloud Neo4j instance credentials (e.g. from [Neo4j AuraDB Free](https://neo4j.com/cloud/platform/aura-graph-database/)).
   - Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.
4. Deploy. Render will automatically build via `pip install -r backend/requirements.txt` and launch `gunicorn --chdir backend app:app`.
5. Access your live website at `https://<your-service-name>.onrender.com/app`.

---

### Option B: Unified Containerized Deployment via Docker Compose
This repository includes `Dockerfile` and `docker-compose.yml`.

To deploy locally or on any cloud VM (AWS EC2, GCP Compute Engine, DigitalOcean Droplet):

```bash
# 1. Clone repository
git clone https://github.com/spranjal-0723/Scholarship-and-Fee-Management-System.git
cd Scholarship-and-Fee-Management-System

# 2. Start both Neo4j and Flask with one command
docker compose up -d --build

# 3. Import schema and sample records into Neo4j
docker exec -i scholarship-neo4j cypher-shell -u neo4j -p scholarship123 < database/neo4j/01_constraints.cypher
docker exec -i scholarship-neo4j cypher-shell -u neo4j -p scholarship123 < database/neo4j/02_import_data.cypher
docker exec -i scholarship-neo4j cypher-shell -u neo4j -p scholarship123 < database/neo4j/03_create_relationships.cypher

# 4. Open browser
# UI: http://localhost:5000/app
# API Status: http://localhost:5000/
# Neo4j Browser: http://localhost:7474/
```

---

### Option C: Production Virtualenv & Gunicorn (Standard Linux VM)

```bash
# 1. Set up Python virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 2. Configure environment
export FLASK_DEBUG=false
export PORT=5000
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-strong-password"
export NEO4J_DATABASE="neo4j"

# 3. Start Gunicorn with 2 worker threads
gunicorn --chdir backend app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
```

---

## 4. Post-Deployment Verification Checklist

Verify the live deployment by executing these HTTP checks against the target domain:

```bash
TARGET_URL="http://localhost:5000"

# 1. Health & Connection check
curl -s "$TARGET_URL/api/neo4j/health"
# Expected: {"database":"neo4j","status":"ok"}

# 2. Web UI check
curl -s -I "$TARGET_URL/app"
# Expected: HTTP/1.1 200 OK, Content-Type: text/html

# 3. Live Dashboard totals
curl -s "$TARGET_URL/api/neo4j/dashboard"
# Expected: {"total_students":5,"total_fees":380000.0,"total_paid":100000.0,...}

# 4. Fee listing
curl -s "$TARGET_URL/api/neo4j/fees?limit=2"
# Expected: {"count":2,"fees":[...]}
```
