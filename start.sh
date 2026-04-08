#!/bin/bash
cd "$(dirname "$0")"

# kill old instances
pkill -f "uvicorn backend.app" 2>/dev/null
pkill -f "vite" 2>/dev/null

# activate conda env with all ML packages
eval "$(conda shell.bash hook)"
conda activate ml

# backend
uvicorn backend.app:app --port 8001 &
BACK=$!

# frontend
cd frontend && npm run dev -- --open &
FRONT=$!

trap "kill $BACK $FRONT 2>/dev/null" EXIT
wait
