#!/bin/bash

# AI Math Tutor - Backend Startup Script

echo "🚀 Starting AI Math Tutor Backend..."
echo ""

# Fix OpenMP duplicate library issue on macOS (for Whisper ASR)
export KMP_DUPLICATE_LIB_OK=TRUE
# Suppress OpenMP deprecation warnings
export KMP_WARNINGS=0

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and start backend
cd backend
source venv/bin/activate

echo "✅ Virtual environment activated"
echo "🔧 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo "💚 Health check: http://localhost:8000/api/health"
echo ""

PYTHONPATH=.. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
