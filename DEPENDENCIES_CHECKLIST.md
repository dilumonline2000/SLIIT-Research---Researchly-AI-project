# Complete Dependencies Checklist

**When setting up on a new laptop, use this checklist to verify all dependencies are installed correctly.**

---

## System Requirements

Before starting, make sure you have:

- [ ] **Node.js 18+** — Check with: `node --version`
- [ ] **npm 9+** — Check with: `npm --version`
- [ ] **Python 3.9+** — Check with: `python --version`
- [ ] **pip** — Check with: `pip --version`
- [ ] **Git** — Check with: `git --version`
- [ ] **~8GB RAM minimum** — ML models need memory
- [ ] **~5GB disk space** — For models + node_modules + venv

---

## Frontend Dependencies (Next.js + React)

**Location**: `apps/web/`

### Install
```bash
cd apps/web
npm install
```

### Dependencies Summary
| Package | Purpose |
|---------|---------|
| next | React framework |
| react, react-dom | UI library |
| @supabase/supabase-js | Database client |
| zustand | State management |
| zod | Data validation |
| tailwindcss | Styling |
| @google/generative-ai | Gemini API client |
| recharts | Charts & graphs |
| lucide-react | Icons |

**Total size**: ~500MB (node_modules)

---

## API Gateway Dependencies (Express.js)

**Location**: `apps/api-gateway/`

### Install
```bash
cd apps/api-gateway
npm install
```

### Dependencies Summary
| Package | Purpose |
|---------|---------|
| express | Web framework |
| axios | HTTP client |
| cors | CORS middleware |
| helmet | Security headers |
| morgan | Request logging |
| @supabase/supabase-js | Database client |
| zod | Data validation |

**Total size**: ~300MB (node_modules)

---

## Python Microservices

Each service has its own virtual environment and requirements.txt.

### Paper-Chat Service

**Location**: `services/paper-chat/`

```bash
cd services/paper-chat
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Key dependencies**:
- fastapi, uvicorn — Web framework
- sentence-transformers — SBERT embeddings
- spacy — NLP (for Citation NER)
- torch — Deep learning (for SBERT)
- pydantic — Data validation
- supabase — Database client

**Size**: ~2.5GB (includes SBERT model cache)

---

### Module 1: Integrity Service

**Location**: `services/module1-integrity/`

```bash
cd services/module1-integrity
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Key dependencies**:
- fastapi, uvicorn
- sentence-transformers
- spacy, transformers
- torch
- scikit-learn
- bertopic, keybert — Topic modeling
- pandas, numpy

**Size**: ~3.5GB (includes trained models + cache)

**Contains trained models**:
- ✓ Citation NER (spaCy) — 150MB
- ✓ SBERT Plagiarism — 500MB

---

### Module 2: Collaboration Service

**Location**: `services/module2-collaboration/`

```bash
cd services/module2-collaboration
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Key dependencies**:
- fastapi, uvicorn
- sentence-transformers
- torch, transformers
- scikit-learn
- datasets, pandas

**Size**: ~2.5GB

**Contains trained models**:
- ✓ Supervisor Matcher SBERT — 600MB

---

### Module 3: Data Management Service

**Location**: `services/module3-data/`

```bash
cd services/module3-data
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Key dependencies**:
- fastapi, uvicorn
- sentence-transformers
- bertopic — Topic modeling
- beautifulsoup4, selenium — Web scraping
- arxiv, scholarly — Academic API clients
- pandas, numpy

**Size**: ~2.5GB

---

### Module 4: Analytics Service

**Location**: `services/module4-analytics/`

```bash
cd services/module4-analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Key dependencies**:
- fastapi, uvicorn
- sentence-transformers
- torch, torch-geometric — Graph neural networks
- xgboost, scikit-learn — ML models
- prophet, statsmodels — Time-series forecasting

**Size**: ~2.0GB

---

## Total Installation Size

| Component | Size | Time |
|-----------|------|------|
| Frontend (apps/web) | 500 MB | 2-3 min |
| API Gateway (apps/api-gateway) | 300 MB | 1-2 min |
| Paper-Chat venv | 2.5 GB | 5-10 min |
| Module 1 venv | 3.5 GB | 10-15 min |
| Module 2 venv | 2.5 GB | 5-10 min |
| Module 3 venv | 2.5 GB | 5-10 min |
| Module 4 venv | 2.0 GB | 5-10 min |
| **TOTAL** | **~16 GB** | **30-60 min** |

---

## Installation Steps (Quick Reference)

### 1️⃣ Frontend
```bash
cd apps/web && npm install && cd ../..
```

### 2️⃣ API Gateway
```bash
cd apps/api-gateway && npm install && cd ../..
```

### 3️⃣ Paper-Chat
```bash
cd services/paper-chat
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 4️⃣ Module 1
```bash
cd services/module1-integrity
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 5️⃣ Module 2
```bash
cd services/module2-collaboration
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 6️⃣ Module 3
```bash
cd services/module3-data
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 7️⃣ Module 4
```bash
cd services/module4-analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

---

## Verification Checklist

After installation, verify everything:

### Node.js packages
```bash
# Check frontend
cd apps/web && npm list | head -20

# Check API Gateway
cd apps/api-gateway && npm list | head -20
```

### Python packages
```bash
# Check paper-chat
cd services/paper-chat
source venv/bin/activate
pip list | grep -E "fastapi|sentence-transformers|torch|spacy"

# Repeat for each module...
```

### Key packages to verify
- [ ] fastapi ✓
- [ ] uvicorn ✓
- [ ] sentence-transformers ✓
- [ ] torch ✓
- [ ] spacy ✓
- [ ] transformers ✓
- [ ] pandas ✓
- [ ] numpy ✓
- [ ] supabase ✓

---

## Common Installation Issues

### Issue 1: "pip install fails for torch"
**Cause**: PyTorch needs specific version for your OS/Python

**Fix**:
```bash
# Try CPU version first (faster install)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Or wait longer for GPU version to compile
```

### Issue 2: "Module not found after pip install"
**Cause**: Virtual environment not activated

**Fix**:
```bash
# Make sure you see (venv) before your prompt
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
```

### Issue 3: "Disk space error during install"
**Cause**: Not enough space for models + cache

**Solution**: Free up 20GB and retry

### Issue 4: "Node modules size is huge"
**Cause**: Normal for monorepo with many dependencies

**Solution**: This is expected (~800MB for both)

### Issue 5: "Import error: No module named spacy"
**Cause**: Pip installed but not in virtual env

**Fix**:
```bash
# Verify venv is active
which python  # Should show path inside venv/

# Reinstall
pip install spacy
```

---

## What to include in ZIP for team member

When creating ZIP file, include:

✅ **Include these:**
- [ ] `apps/` directory
- [ ] `services/` directory
- [ ] `ml/` directory (scripts + data)
- [ ] `TEAM_SETUP_GUIDE.md`
- [ ] `DEPENDENCIES_CHECKLIST.md`
- [ ] `COMPLETE_FIX_GUIDE.md`
- [ ] `.env.example` files
- [ ] `package.json` and `requirements.txt` files
- [ ] Git history (for commits)
- [ ] Trained models in `services/module1-integrity/models/`

❌ **DO NOT include:**
- [ ] `node_modules/` directories (each 500MB+)
- [ ] Python `venv/` directories (each 2-3GB)
- [ ] `__pycache__/` directories
- [ ] `.next/` build directory
- [ ] `.env` files with real secrets (use `.env.example` instead)

**ZIP file size**: ~2-3GB (including models)

---

## After Installation

Once all dependencies are installed:

1. ✓ Set up `.env` files with Supabase credentials
2. ✓ Start 4 services in 4 different terminals (see TEAM_SETUP_GUIDE.md)
3. ✓ Verify at http://localhost:3000
4. ✓ Check models loaded at `/settings`

You're ready to go! 🎉

---

## Questions?

If pip/npm install fails:
1. Check error message carefully
2. Search error in documentation
3. Try installing one package at a time
4. Contact Kariyawasam with the error message
