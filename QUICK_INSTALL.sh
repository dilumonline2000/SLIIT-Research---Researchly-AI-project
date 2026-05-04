#!/bin/bash
# Quick Install Script for Researchly AI
# Usage: bash QUICK_INSTALL.sh
# This will install all dependencies for frontend + 5 Python services

set -e  # Exit on error

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  RESEARCHLY AI — QUICK INSTALL                                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "[1/7] Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install from nodejs.org"; exit 1; }
command -v python >/dev/null 2>&1 || { echo "❌ Python not found. Install from python.org"; exit 1; }
echo "✓ Node.js: $(node --version)"
echo "✓ Python: $(python --version)"
echo ""

# Frontend
echo "[2/7] Installing Frontend (Next.js)..."
cd apps/web
npm install >/dev/null 2>&1 && echo "✓ Frontend installed" || echo "❌ Frontend install failed"
cd ../..
echo ""

# API Gateway
echo "[3/7] Installing API Gateway (Express)..."
cd apps/api-gateway
npm install >/dev/null 2>&1 && echo "✓ API Gateway installed" || echo "❌ API Gateway install failed"
cd ../..
echo ""

# Paper-Chat
echo "[4/7] Installing Paper-Chat Service..."
cd services/paper-chat
python -m venv venv >/dev/null 2>&1
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate
pip install -r requirements.txt >/dev/null 2>&1 && echo "✓ Paper-Chat installed" || echo "❌ Paper-Chat install failed"
cd ../..
echo ""

# Module 1
echo "[5/7] Installing Module 1 (Integrity)..."
cd services/module1-integrity
python -m venv venv >/dev/null 2>&1
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate
pip install -r requirements.txt >/dev/null 2>&1 && echo "✓ Module 1 installed" || echo "❌ Module 1 install failed"
cd ../..
echo ""

# Module 2
echo "[6/7] Installing Module 2 (Collaboration)..."
cd services/module2-collaboration
python -m venv venv >/dev/null 2>&1
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate
pip install -r requirements.txt >/dev/null 2>&1 && echo "✓ Module 2 installed" || echo "❌ Module 2 install failed"
cd ../..
echo ""

# Module 3
echo "[7/7] Installing Module 3 (Data Management)..."
cd services/module3-data
python -m venv venv >/dev/null 2>&1
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate
pip install -r requirements.txt >/dev/null 2>&1 && echo "✓ Module 3 installed" || echo "❌ Module 3 install failed"
cd ../..
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  INSTALLATION COMPLETE! ✓                                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "Next steps:"
echo ""
echo "1. Set up environment variables:"
echo "   - Copy apps/web/.env.example → apps/web/.env.local"
echo "   - Copy services/.env.example → services/.env"
echo "   - Fill in SUPABASE_URL and API keys"
echo ""
echo "2. Start 4 services in 4 separate terminals:"
echo "   Terminal 1: cd apps/web && npm run dev"
echo "   Terminal 2: cd apps/api-gateway && npm run dev"
echo "   Terminal 3: cd services/paper-chat && source venv/bin/activate && python -m uvicorn app.main:app --reload --port 8005"
echo "   Terminal 4: cd services/module1-integrity && source venv/bin/activate && python -m uvicorn app.main:app --reload --port 8002"
echo ""
echo "3. Open browser: http://localhost:3000"
echo ""
echo "For detailed instructions, see: TEAM_SETUP_GUIDE.md"
echo ""
