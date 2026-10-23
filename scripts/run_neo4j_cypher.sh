#!/usr/bin/env bash
# ==============================================================================
# Run All Neo4j Cypher Schema & Seeding Scripts
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================================="
echo "Initializing Neo4j Graph Database Schema & Constraints"
echo "=========================================================="

if [ -f "$ROOT_DIR/backend/venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/backend/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "Running idempotent graph seeder via $PYTHON_BIN..."
$PYTHON_BIN "$SCRIPT_DIR/seed_demo_data.py" --engine neo4j

echo "✓ Neo4j Graph Database 5.26 nodes, relationships, and constraints loaded."
