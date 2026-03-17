#!/bin/bash
# Track Triumph Pro — Start Script
# Starts both the FastAPI backend and serves the frontend

echo "🏇 Track Triumph Pro — Starting..."
echo ""

# Load env vars
if [ -f backend/.env ]; then
  export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Start FastAPI backend
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2
echo "✅ Backend running on http://localhost:8000"
echo "📄 API docs: http://localhost:8000/docs"

# Serve frontend
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend running on http://localhost:3000"
echo ""
echo "🚀 Pages:"
echo "   Landing Page:  http://localhost:3000/index.html"
echo "   Dashboard:     http://localhost:3000/dashboard.html"
echo "   Admin Panel:   http://localhost:3000/admin.html"
echo "   Business Hub:  http://localhost:3000/business.html"
echo "   Pitch Deck:    http://localhost:3000/deck/"
echo "   Terms:         http://localhost:3000/terms.html"
echo "   Privacy:       http://localhost:3000/privacy.html"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
