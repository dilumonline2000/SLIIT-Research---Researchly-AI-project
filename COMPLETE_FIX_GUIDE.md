# Complete Fix Guide - Local Models + Gemini Setup

## Problem
- Application runs but trained models don't load
- Can't switch from Gemini to Local AI
- Gemini not working either
- Everything broken after cloning from GitHub

## Solution: Step by Step

---

## STEP 1: Verify Trained Models Exist

Run this to check:
```bash
cd "d:/SLIIT Research - Researchly AI project"

# Check if models are there
ls services/module1-integrity/models/

# You should see:
# citation_ner/
# sbert_plagiarism/
```

If they DON'T exist, **train them first**:
```bash
cd services/module1-integrity

# Train Citation NER
python ml/training/train_citation_ner.py --epochs 15

# Train SBERT Plagiarism
python ml/training/train_sbert.py --output services/module1-integrity/models/sbert_plagiarism --epochs 15
```

---

## STEP 2: Setup Environment Variables

### For Gemini to work:

**File**: `apps/web/.env.local`

Make sure you have:
```env
NEXT_PUBLIC_GEMINI_API_KEY=your-actual-gemini-api-key
```

**Get API Key**:
1. Go: https://makersuite.google.com/app/apikeys
2. Create new API key
3. Copy and paste it in `.env.local`

### For Backend Services:

**File**: `services/.env`

Make sure you have:
```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-key
SUPABASE_SERVICE_ROLE_KEY=your-key
```

---

## STEP 3: Install Dependencies

```bash
# Frontend
cd apps/web
npm install

# Backend services
cd services/paper-chat
pip install -r requirements.txt

cd services/module1-integrity
pip install -r requirements.txt
```

---

## STEP 4: Start All Services

**Terminal 1: Frontend**
```bash
cd apps/web
npm run dev
# Should start at http://localhost:3000
```

**Terminal 2: API Gateway**
```bash
cd apps/api-gateway
npm run dev
# Should start at http://localhost:3000 (same port, proxies to backend)
```

**Terminal 3: Paper-Chat Service (Loads models)**
```bash
cd services/paper-chat
python -m uvicorn app.main:app --reload --port 8005

# Should see in logs:
# [Model Loader] [+] Citation NER loaded
# [Model Loader] [+] SBERT Plagiarism loaded
```

**Terminal 4: Module 1 Service**
```bash
cd services/module1-integrity
python -m uvicorn app.main:app --reload --port 8002
```

---

## STEP 5: Verify Everything Works

### Check 1: Models Are Loaded
```bash
# In browser console (F12)
fetch('/api/v1/ai/local/health')
  .then(r => r.json())
  .then(d => console.log(d))

# Should show:
# available: true
# models: { citation_ner: {loaded: true}, sbert_plagiarism: {loaded: true}, ... }
```

### Check 2: Settings Page
1. Go: http://localhost:3000/settings
2. Should show: **"Local models ready: 2/10"**
3. Citation NER: [TRAINED] ✓
4. SBERT Plagiarism: [TRAINED] ✓

### Check 3: Can Toggle to Local
1. Click AI Provider Toggle
2. Should switch: Gemini → Local Models ✓

### Check 4: Gemini Works
1. Go to any chat
2. Make sure toggle is set to "Gemini"
3. Ask a question
4. Should get response from Gemini ✓

### Check 5: Local Models Work
1. Toggle to "Local Models"
2. Go to Integrity Chat
3. Test Citation NER: Paste a citation, ask to parse it
4. Should extract authors, title, year ✓

---

## STEP 6: If Something Still Doesn't Work

### Models Not Loading?
```bash
# Check if paper-chat is running
# Should see in terminal:
# [Model Loader] [+] Citation NER loaded (F1=99.45%)
# [Model Loader] [+] SBERT Plagiarism loaded (Accuracy=100%)

# If not, manually test:
cd services/paper-chat
python -c "
import sys
sys.path.insert(0, '../../services')
from app.services.model_loader import load_all_trained_models
results = load_all_trained_models()
print('Results:', results)
"
```

### Gemini Not Working?
```bash
# Check if API key is set
# In browser console:
console.log(process.env.NEXT_PUBLIC_GEMINI_API_KEY)

# Should show your key (not undefined/null)

# If empty, update apps/web/.env.local and restart npm
```

### Can't Toggle to Local?
```bash
# Check if health endpoint is working
curl http://localhost:3000/api/v1/ai/local/health

# Should return: {"available": true, "models": {...}}

# If error, make sure paper-chat service is running (port 8005)
```

### Toggle Switches But Models Not Used?
```bash
# Check localStorage
# In browser console:
localStorage.getItem('aiProvider')

# Should show: 'local' after you toggle

# If it doesn't change, there's a frontend state issue
# Try: localStorage.setItem('aiProvider', 'local') and refresh
```

---

## Quick Checklist

Before you test, verify:

- [ ] Trained models exist: `services/module1-integrity/models/`
- [ ] Citation NER model: `citation_ner/config.cfg` exists
- [ ] SBERT model: `sbert_plagiarism/model.safetensors` exists
- [ ] Gemini API key in: `apps/web/.env.local`
- [ ] Frontend running: `npm run dev` (Terminal 1)
- [ ] API Gateway running (Terminal 2)
- [ ] Paper-Chat running: Shows model loading logs (Terminal 3)
- [ ] Module 1 running: port 8002 (Terminal 4)
- [ ] Settings page shows: "Local models ready: 2/10"
- [ ] Can toggle to Local Models
- [ ] Can ask questions in Gemini mode
- [ ] Can ask questions in Local mode (gets responses in <2 sec)

---

## If All Else Fails: Nuclear Reset

```bash
# 1. Kill all services
# Close all terminals

# 2. Clean everything
cd apps/web
rm -rf node_modules
npm install

cd apps/api-gateway
rm -rf node_modules
npm install

# 3. Clean Python cache
cd services/paper-chat
rm -rf __pycache__ .pytest_cache
pip install -r requirements.txt --force-reinstall

cd services/module1-integrity
rm -rf __pycache__ .pytest_cache
pip install -r requirements.txt --force-reinstall

# 4. Start fresh (from Step 4 above)
# Make sure API keys are set first!
```

---

## What Each Service Does

| Service | Port | Purpose |
|---------|------|---------|
| Frontend (Next.js) | 3000 | Web UI, settings, chat |
| API Gateway | 3000 | Proxies to backend services |
| Paper-Chat | 8005 | Loads models, health endpoint |
| Module 1 | 8002 | Citation, plagiarism endpoints |

---

## Troubleshooting Map

| Problem | Check |
|---------|-------|
| Models say "Not trained" | Verify `services/module1-integrity/models/` exists with model files |
| Can't toggle to Local | Check `/api/v1/ai/local/health` returns `available: true` |
| Gemini gives no response | Check `NEXT_PUBLIC_GEMINI_API_KEY` in `apps/web/.env.local` |
| Local models give no response | Check paper-chat running on 8005 and models loaded in logs |
| Settings page broken | Check API Gateway running and accessible |
| Slow responses in Local mode | Check if using GPU (should be fast: <1-2 sec) |

---

## Final Test Workflow

1. **Verify models exist**: `ls services/module1-integrity/models/`
2. **Start all services**: 4 terminals (Frontend, Gateway, Paper-Chat, Module1)
3. **Check health**: http://localhost:3000/settings → "Local models ready: 2/10"
4. **Test Gemini**: Ask a question → Get response
5. **Test Local**: Toggle to Local → Ask a question → Get response in <2 sec
6. **Test Citation NER**: Paste citation → Parse → See extracted fields
7. **Test SBERT**: Paste 2 texts → Check similarity

**Everything should work now!** 🎉

---

## Need Help?

If still broken, check:
1. All 4 services running (check 4 terminals)
2. All API keys set (check `.env` files)
3. Models actually exist (check file system)
4. Browser dev console for errors (F12)
5. Service terminal logs for errors

Then post error message and we'll fix it!
