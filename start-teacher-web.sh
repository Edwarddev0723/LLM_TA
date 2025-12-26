#!/bin/bash

# AI Math Tutor - Teacher/Parent Web Portal Startup Script

echo "🚀 Starting AI Math Tutor Teacher/Parent Portal (Vue)..."
echo ""

# Check if node_modules exists
if [ ! -d "apps/teacher-web/node_modules" ]; then
    echo "❌ node_modules not found!"
    echo "Please run: cd apps/teacher-web && npm install"
    exit 1
fi

cd apps/teacher-web

echo "✅ Dependencies found"
echo "🔧 Starting Vite dev server on http://localhost:5173"
echo "🔗 API proxy configured: /api -> http://localhost:8000/api"
echo ""

npm run dev
