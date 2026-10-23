#!/usr/bin/env bash
# ==============================================================================
# Run All Oracle SQL & PL/SQL Scripts
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================================="
echo "Initializing Oracle Database Schema & Seed Data"
echo "=========================================================="

if [ -f "$ROOT_DIR/backend/venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/backend/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "Running idempotent database seeder via $PYTHON_BIN..."
$PYTHON_BIN "$SCRIPT_DIR/seed_demo_data.py" --engine oracle

echo "✓ Oracle Database 23ai Free tables, constraints, views, and data loaded."
