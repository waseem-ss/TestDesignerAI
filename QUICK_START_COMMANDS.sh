#!/bin/bash
# TestDesignerAI - Quick Start Commands
# Phase A + B Ready

echo "🚀 TestDesignerAI Quick Start"
echo "=============================="
echo ""

# Step 1: Check Python
echo "✓ Checking Python installation..."
python --version

# Step 2: Create/activate virtual environment
echo ""
echo "✓ Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate venv (adjust for Windows if needed)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# Step 3: Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install -r requirements.txt --quiet

# Step 4: Check environment
echo ""
echo "✓ Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env file - Please add your API keys:"
    echo "  - GROQ_API_KEY (from https://console.groq.com)"
    echo "  - OPENAI_API_KEY (optional)"
    echo "  - ANTHROPIC_API_KEY (optional)"
fi

echo ""
echo "=============================="
echo "✅ Setup Complete!"
echo ""
echo "📋 TO RUN THE SYSTEM:"
echo ""
echo "Terminal 1 (API Server):"
echo "  python -m api.api"
echo "  → Open: http://localhost:8000/docs"
echo ""
echo "Terminal 2 (Dashboard):"
echo "  streamlit run frontend/dashboard.py"
echo "  → Open: http://localhost:8501"
echo ""
echo "📊 QUICK TESTS:"
echo ""
echo "Health Check:"
echo "  curl http://localhost:8000/api/health"
echo ""
echo "Process a requirement:"
echo "  curl -X POST http://localhost:8000/api/process \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"req_id\": \"TEST_001\", \"text\": \"Test requirement\"}'"
echo ""
echo "=============================="
