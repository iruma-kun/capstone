#!/bin/bash
echo "Starting Enterprise FinTech Intelligence Platform..."
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run installation steps first."
    exit 1
fi

echo "Launching FastAPI Backend on http://localhost:8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
