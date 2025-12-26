#!/bin/bash

# AI Math Tutor - Student Frontend Startup Script

echo "🚀 Starting AI Math Tutor Student Frontend (React)..."
echo ""

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ node_modules not found!"
    echo "Please run: cd frontend && npm install"
    exit 1
fi

cd frontend

echo "✅ Dependencies found"
echo "🔧 Starting Vite dev server on http://localhost:5173"
echo "🔗 API proxy configured: /api -> http://localhost:8000/api"
echo ""

npm run dev
