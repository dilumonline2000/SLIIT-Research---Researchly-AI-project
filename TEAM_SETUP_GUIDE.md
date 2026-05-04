# Researchly AI — Team Installation & Setup Guide

**For team members receiving the ZIP file and setting up on their laptop**

---

## Quick Overview

This is a full-stack AI research paper assistant with:
- **Frontend**: Next.js 14 (React + TypeScript)
- **Backend**: Express.js API Gateway + 4 Python FastAPI microservices
- **Database**: Supabase (PostgreSQL + pgvector)
- **ML Models**: Trained Citation NER, SBERT Plagiarism detection, and more

---

## Step 1: Extract ZIP and Check Project Structure

```bash
# After extracting ZIP
cd "Researchly AI"
ls -la

# You should see:
# apps/
# services/
# ml/
# .env files
# package.json files
# requirements.txt files
```

---

## Step 2: Install All Dependencies

### Frontend & API Gateway (Node.js)

**Requirements**: Node.js 18+ and npm/pnpm

```bash
# Install frontend dependencies
cd apps/web
npm install
# OR use pnpm (faster):
# pnpm install

# Go back to root
cd ../..

# Install API Gateway dependencies
cd apps/api-gateway
npm install

# Back to root again
cd ../..
```

### Python Microservices

**Requirements**: Python 3.9+, pip, and virtual environment

```bash
# Paper Chat Service
cd services/paper-chat
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Module 1 — Integrity Service
cd ../module1-integrity
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Module 2 — Collaboration Service
cd ../module2-collaboration
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Module 3 — Data Management Service
cd ../module3-data
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Module 4 — Analytics Service
cd ../module4-analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Go back to root
cd ../..
```

---

## Step 3: Set Up Environment Variables

### Frontend (.env.local)

**File**: `apps/web/.env.local`

```env
# Supabase (ask Kariyawasam for these)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Google Gemini API (get from https://makersuite.google.com/app/apikeys)
NEXT_PUBLIC_GEMINI_API_KEY=your-gemini-api-key
```

### Backend Services (.env)

**File**: `services/.env`

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
```

**Get these values from**:
1. Supabase Dashboard → Project Settings → API
2. Ask Kariyawasam if you don't have access

---

## Step 4: Check Trained Models Exist

Before starting services, verify the trained models are in the ZIP:

```bash
# Check Citation NER model
ls services/module1-integrity/models/citation_ner/

# You should see: config.cfg, meta.json, model-best/, tokenizer.json

# Check SBERT Plagiarism model
ls services/module1-integrity/models/sbert_plagiarism/

# You should see: config.json, model.safetensors, sentence_bert_config.json, etc.
```

**If models are missing**, ask Kariyawasam to include them (they're large ~500MB total).

---

## Step 5: Start All Services (4 Terminals)

Open **4 separate terminal windows** in the project root. Each service runs independently.

### Terminal 1: Frontend (Next.js)

```bash
cd apps/web
npm run dev
# Should start at http://localhost:3000
```

### Terminal 2: API Gateway

```bash
cd apps/api-gateway
npm run dev
# Should start at http://localhost:8000 (proxies to backend)
```

### Terminal 3: Paper-Chat Service (Loads trained models)

```bash
cd services/paper-chat
source venv/bin/activate  # Activate virtual environment
python -m uvicorn app.main:app --reload --port 8005

# Should show in logs:
# [Model Loader] [+] Citation NER loaded
# [Model Loader] [+] SBERT Plagiarism loaded
```

### Terminal 4: Module 1 Service (Integrity)

```bash
cd services/module1-integrity
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8002
```

---

## Step 6: Verify Everything Works

### Check 1: Frontend is running
- Open browser: **http://localhost:3000**
- Should see Researchly AI dashboard

### Check 2: Models are loaded
- Open browser console (F12) and run:
```javascript
fetch('/api/v1/ai/local/health')
  .then(r => r.json())
  .then(d => console.log(d))

// Should show:
// { available: true, models: { citation_ner: {loaded: true}, sbert_plagiarism: {loaded: true}, ... } }
```

### Check 3: Settings page shows model status
1. Go to **http://localhost:3000/settings**
2. Scroll to "AI Provider Settings"
3. Should show: **"Local models ready: 2/10"**
4. Citation NER: [TRAINED] ✓
5. SBERT Plagiarism: [TRAINED] ✓

### Check 4: Can toggle between Gemini and Local
1. In settings, look for "AI Provider Toggle"
2. Should be able to switch: Gemini ↔ Local Models
3. After toggle, refresh page to verify choice persists

---

## Step 7: Test Functionality

### Test Citation Extraction (Local Model)

1. Go to **http://localhost:3000/module-1/citations**
2. Paste a citation:
```
De Silva, M., Vilasa, S., Bandara, A (2022). Impact of Terminal Handling Charges on the Performance of Non-Vessel Operating Common Carriers.
```
3. Click "Parse Citation"
4. Should extract: Authors, Title, Year

### Test Plagiarism Detection (Local Model)

1. Go to **http://localhost:3000/module-1/plagiarism**
2. Paste two texts
3. Should show similarity score (0-100%)

### Test with Gemini

1. Toggle to "Gemini" mode
2. Go to any chat
3. Ask a question
4. Should get response from Google Gemini API

---

## Troubleshooting

### Problem: "Models not showing as loaded"
**Solution**: Check if paper-chat service is running on port 8005
```bash
curl http://localhost:8005/local/health
```

### Problem: "Can't see local models in settings"
**Solution**: Make sure API Gateway is running on port 8000
```bash
curl http://localhost:8000/api/v1/ai/local/health
```

### Problem: "Gemini not responding"
**Solution**: Check if NEXT_PUBLIC_GEMINI_API_KEY is set in `apps/web/.env.local`
```javascript
console.log(process.env.NEXT_PUBLIC_GEMINI_API_KEY)
// Should show key, not undefined
```

### Problem: "Python pip install fails"
**Solution**: Make sure you're inside virtual environment
```bash
# Check if (venv) appears in terminal before your command
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Problem: "Port already in use"
**Solution**: Kill existing process or use different port
```bash
# Linux/Mac
lsof -i :3000
kill -9 <PID>

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## Command Summary (Copy-Paste for Quick Setup)

```bash
# Install everything (run from root directory)

# Frontend
cd apps/web && npm install && cd ../..

# API Gateway
cd apps/api-gateway && npm install && cd ../..

# Paper Chat
cd services/paper-chat && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ../..

# Module 1
cd services/module1-integrity && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ../..

# Module 2
cd services/module2-collaboration && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ../..

# Module 3
cd services/module3-data && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ../..

# Module 4
cd services/module4-analytics && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ../..
```

Then open 4 terminals and start each service as shown in **Step 5**.

---

## Questions? Ask Kariyawasam

If anything fails:
1. Check the troubleshooting section above
2. Look at error messages in terminal
3. Check browser console (F12) for frontend errors
4. Verify all 4 services are running
5. Contact Kariyawasam with error message and which terminal it appears in

---

**You're all set!** 🎉 The application should be running with local trained models ready to use.
