#!/bin/bash
set -e
cd "$(dirname "$0")"

# ── 0. Detect OS ─────────────────────────────────────────────────────────────
case "$(uname -s)" in
  CYGWIN*|MINGW*|MSYS*) IS_WINDOWS=true ;;
  *)                     IS_WINDOWS=false ;;
esac

# ── 1. Check for Python 3.10+ ───────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌  Python 3 is required but not found. Install it from https://www.python.org/downloads/"
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "❌  Python 3.10+ is required (found $PY_VERSION)"
  exit 1
fi
if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 13 ]; then
  echo "⚠️   Python $PY_VERSION detected — numba/llvmlite may not have wheels for this version."
  echo "    If pip install fails, use Python 3.10–3.12 instead."
fi
echo "✅  Python $PY_VERSION"

# ── 2. Create / activate virtual environment ─────────────────────────────────
if [ ! -d ".venv" ]; then
  echo "📦  Creating virtual environment…"
  python3 -m venv .venv
fi
if [ "$IS_WINDOWS" = true ]; then
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi
echo "✅  Virtual environment activated"

# ── 3. Install Python dependencies ───────────────────────────────────────────
echo "📦  Installing Python dependencies…"
pip install --upgrade pip -q

# Pre-install llvmlite/numba with binary-only wheels (never compile from source)
SHAP_OK=true
if ! pip install llvmlite numba --only-binary :all: -q 2>/dev/null; then
  echo "⚠️   No pre-built llvmlite/numba wheel for Python $PY_VERSION on $(uname -m)."
  echo "    Skipping SHAP — install Python 3.10–3.12 for full support."
  SHAP_OK=false
fi

if [ "$SHAP_OK" = true ]; then
  if ! pip install -r requirements.txt -q; then
    echo ""
    echo "❌  pip install failed."
    echo "    Trying to install everything except shap/numba…"
    pip install $(grep -v -E '^(shap|numba)' requirements.txt | grep -v '^#' | grep -v '^$') -q
    SHAP_OK=false
  fi
else
  pip install $(grep -v -E '^(shap|numba)' requirements.txt | grep -v '^#' | grep -v '^$') -q
fi

if [ "$SHAP_OK" = false ]; then
  echo "⚠️   Installed without SHAP. SHAP-based explanations will be unavailable."
fi
echo "✅  Python dependencies installed"

# ── 4. Check for Node.js (needed for frontend) ──────────────────────────────
if ! command -v node &>/dev/null; then
  echo "❌  Node.js is required but not found."
  echo "   Install it from https://nodejs.org/ (LTS recommended)"
  exit 1
fi
echo "✅  Node $(node -v)"

# ── 5. Install frontend dependencies ────────────────────────────────────────
if [ ! -d "frontend/node_modules" ]; then
  echo "📦  Installing frontend dependencies…"
  (cd frontend && npm install)
fi
echo "✅  Frontend dependencies ready"

# ── 6. Kill old instances (scoped to this project) ───────────────────────────
pkill -f "uvicorn backend.app:app --port 8001" 2>/dev/null || true
lsof -ti:8001 2>/dev/null | xargs kill 2>/dev/null || true

# ── 7. Start backend & frontend ─────────────────────────────────────────────
echo ""
echo "🚀  Starting backend on http://localhost:8001"
echo "🚀  Starting frontend (Vite dev server)…"
echo ""

uvicorn backend.app:app --port 8001 &
BACK=$!

(cd frontend && npm run dev) &
FRONT=$!

trap "kill $BACK $FRONT 2>/dev/null" EXIT
wait
