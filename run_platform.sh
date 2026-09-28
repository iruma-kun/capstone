#!/bin/bash
echo "Starting Cloud-Native Automated Compliance and Audit Platform..."
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run installation steps first."
    exit 1
fi

echo "Launching FastAPI Compliance API on http://localhost:8000..."
echo "Interactive API Documentation: http://localhost:8000/docs"

# Run seeding in background after a short delay
(sleep 3 && curl -X POST http://localhost:8000/api/seed-samples > /dev/null 2>&1 && echo "Sample documents seeded.") &

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
