# ZIP File Packing Checklist

**Before sharing with team members, verify all necessary files are in the ZIP.**

---

## Files to INCLUDE (Essential)

### Documentation
- [x] `TEAM_SETUP_GUIDE.md` — Main setup instructions
- [x] `DEPENDENCIES_CHECKLIST.md` — Detailed dependency list
- [x] `COMPLETE_FIX_GUIDE.md` — Troubleshooting guide
- [x] `QUICK_INSTALL.sh` — Automated install script (Mac/Linux)
- [x] `QUICK_INSTALL.bat` — Automated install script (Windows)
- [x] `README.md` — Project overview (if exists)

### Configuration
- [x] `apps/web/.env.example` — Frontend config template
- [x] `services/.env.example` — Backend config template
- [x] `.gitignore` — To prevent committing secrets

### Frontend
- [x] `apps/web/` — Complete Next.js project
- [x] `apps/web/package.json` — Dependencies
- [x] `apps/web/src/` — Source code
- [x] `apps/web/public/` — Static assets
- [x] `.gitignore` (in web folder)
- [x] `tsconfig.json` — TypeScript config

### API Gateway
- [x] `apps/api-gateway/` — Express.js gateway
- [x] `apps/api-gateway/package.json` — Dependencies
- [x] `apps/api-gateway/src/` — Source code
- [x] `tsconfig.json` — TypeScript config

### Backend Services
- [x] `services/paper-chat/` — Complete service
- [x] `services/paper-chat/requirements.txt` — Python deps
- [x] `services/paper-chat/app/` — Source code
- [x] `services/module1-integrity/` — Complete service
- [x] `services/module1-integrity/requirements.txt` — Python deps
- [x] `services/module1-integrity/app/` — Source code
- [x] `services/module2-collaboration/` — Complete service
- [x] `services/module2-collaboration/requirements.txt` — Python deps
- [x] `services/module3-data/` — Complete service
- [x] `services/module3-data/requirements.txt` — Python deps
- [x] `services/module4-analytics/` — Complete service
- [x] `services/module4-analytics/requirements.txt` — Python deps
- [x] `services/shared/` — Shared utilities

### Machine Learning
- [x] `ml/data/` — Training data
- [x] `ml/scripts/` — Data processing scripts
- [x] `ml/training/` — Training scripts
- [x] `services/module1-integrity/models/citation_ner/` — **TRAINED MODEL** (150MB)
- [x] `services/module1-integrity/models/sbert_plagiarism/` — **TRAINED MODEL** (500MB)
- [x] `services/module2-collaboration/models/trained_supervisor_matcher/` — **TRAINED MODEL** (600MB)

### Git & Config
- [x] `.git/` — Full git history (for commits/logs)
- [x] `.github/` — GitHub workflows (if any)
- [x] `.gitignore` — In each directory
- [x] `package.json` — Root monorepo config (if exists)

---

## Files to EXCLUDE (Do NOT include)

### Node.js
- [ ] ❌ `node_modules/` — EVERYWHERE (500MB+ each)
- [ ] ❌ `.next/` — Build directory (apps/web)
- [ ] ❌ `dist/` — Compiled output (apps/api-gateway)

### Python
- [ ] ❌ `venv/` — Virtual environments (2-3GB each)
- [ ] ❌ `.venv/` — Alternative venv name
- [ ] ❌ `__pycache__/` — Python cache (everywhere)
- [ ] ❌ `*.pyc` — Compiled Python files
- [ ] ❌ `.pytest_cache/` — Test cache
- [ ] ❌ `*.egg-info/` — Package metadata

### Secrets & Private
- [ ] ❌ `.env` — Real secrets (use .env.example instead)
- [ ] ❌ `.env.local` — Real secrets
- [ ] ❌ `secrets/` — Any secrets folder
- [ ] ❌ Private API keys in code

### System
- [ ] ❌ `.DS_Store` — Mac system files
- [ ] ❌ `Thumbs.db` — Windows system files
- [ ] ❌ `.vs/` — VS Code cache
- [ ] ❌ `.idea/` — IDE cache

### Large Files
- [ ] ❌ `*.zip` — Don't nest zips
- [ ] ❌ Raw model files > 1GB (use trained versions in `models/`)

---

## Directory Structure to Include

```
Researchly-AI/
├── TEAM_SETUP_GUIDE.md              ← START HERE
├── DEPENDENCIES_CHECKLIST.md
├── COMPLETE_FIX_GUIDE.md
├── ZIP_PACKING_CHECKLIST.md
├── QUICK_INSTALL.sh
├── QUICK_INSTALL.bat
├── .gitignore
├── .env.example
│
├── apps/
│   ├── web/
│   │   ├── package.json             ✓ Include
│   │   ├── src/                     ✓ Include
│   │   ├── public/                  ✓ Include
│   │   ├── .env.example             ✓ Include
│   │   ├── tsconfig.json
│   │   └── node_modules/            ✗ EXCLUDE
│   │
│   └── api-gateway/
│       ├── package.json             ✓ Include
│       ├── src/                     ✓ Include
│       ├── tsconfig.json
│       ├── dist/                    ✗ EXCLUDE
│       └── node_modules/            ✗ EXCLUDE
│
├── services/
│   ├── paper-chat/
│   │   ├── requirements.txt         ✓ Include
│   │   ├── app/                     ✓ Include
│   │   └── venv/                    ✗ EXCLUDE
│   │
│   ├── module1-integrity/
│   │   ├── requirements.txt         ✓ Include
│   │   ├── app/                     ✓ Include
│   │   ├── models/
│   │   │   ├── citation_ner/        ✓ INCLUDE (150MB)
│   │   │   └── sbert_plagiarism/    ✓ INCLUDE (500MB)
│   │   ├── data/                    ✓ Include
│   │   └── venv/                    ✗ EXCLUDE
│   │
│   ├── module2-collaboration/
│   │   ├── requirements.txt         ✓ Include
│   │   ├── app/                     ✓ Include
│   │   ├── models/
│   │   │   └── trained_supervisor_matcher/  ✓ INCLUDE (600MB)
│   │   └── venv/                    ✗ EXCLUDE
│   │
│   ├── module3-data/
│   │   ├── requirements.txt         ✓ Include
│   │   ├── app/                     ✓ Include
│   │   └── venv/                    ✗ EXCLUDE
│   │
│   ├── module4-analytics/
│   │   ├── requirements.txt         ✓ Include
│   │   ├── app/                     ✓ Include
│   │   └── venv/                    ✗ EXCLUDE
│   │
│   ├── shared/                      ✓ Include
│   └── .env.example                 ✓ Include
│
├── ml/
│   ├── data/                        ✓ Include
│   ├── scripts/                     ✓ Include
│   └── training/                    ✓ Include
│
└── .git/                            ✓ Include (git history)
```

---

## How to Create ZIP File

### On Mac/Linux

```bash
# Navigate to parent directory of Researchly-AI
cd ..

# Create ZIP excluding unnecessary files
zip -r -x "*/node_modules/*" "*/venv/*" "*/__pycache__/*" "*.pyc" ".next/*" "dist/*" \
  Researchly-AI.zip Researchly-AI/

# Check size
ls -lh Researchly-AI.zip
```

### On Windows (Using 7-Zip)

1. Right-click "Researchly-AI" folder
2. Select "7-Zip" → "Add to archive..."
3. In "Archive name", type: `Researchly-AI.zip`
4. In "Compression level", select "Fast"
5. Click "Add"

### Using Python

```bash
python -c "
import shutil
import os

exclude = {'node_modules', 'venv', '__pycache__', '.next', 'dist'}

def zipignore(folder, files):
    return [f for f in files if f in exclude]

shutil.make_archive('Researchly-AI', 'zip', '.', 'Researchly-AI', ignore=zipignore)
print('ZIP created: Researchly-AI.zip')
"
```

---

## Expected ZIP File Size

```
Frontend (apps/web/) ...................... ~50 MB
API Gateway (apps/api-gateway/) ........... ~30 MB
Paper-Chat service ....................... ~100 MB
Module 1 service ......................... ~150 MB
Module 1 trained models .................. ~650 MB
Module 2 service + models ................ ~250 MB
Module 3 & 4 services .................... ~100 MB
Documentation + scripts .................. ~10 MB
ML data & training scripts ............... ~150 MB
.git history ............................ ~50 MB
───────────────────────────────────────────────
TOTAL ............................... ~1.5 - 2 GB
```

**Note**: Trained models (Citation NER, SBERT, Supervisor Matcher) are **included**. This is essential so team member doesn't need to re-train them (which takes 2+ hours).

---

## Before Sharing ZIP

### Verification Checklist

Run these commands from project root to verify:

```bash
# Check trained models exist
ls -la services/module1-integrity/models/citation_ner/
ls -la services/module1-integrity/models/sbert_plagiarism/
ls -la services/module2-collaboration/models/trained_supervisor_matcher/

# Check no secrets leaked
grep -r "SUPABASE_SERVICE_ROLE_KEY" apps/ services/ --include="*.py" --include="*.ts" --include="*.js"

# Should output nothing (no secrets in code)
```

### Remove Secrets Before Zipping

```bash
# Make sure .env files are NOT included, only .env.example
find . -name ".env" -not -name ".env.example" -type f

# These should be empty or show only .env.example files
```

---

## What Team Member Should Do After Extracting

1. **Read** `TEAM_SETUP_GUIDE.md` first
2. **Run** `QUICK_INSTALL.sh` (Mac/Linux) or `QUICK_INSTALL.bat` (Windows)
3. **Set up** `.env` files from `.env.example` templates
4. **Start** 4 services in 4 terminals
5. **Open** http://localhost:3000 in browser

**Time to get running**: ~45 minutes (30 min install + 15 min setup)

---

## Hosting/Sharing ZIP

### Best Options

1. **OneDrive/Google Drive** — Easiest for shared access
2. **GitHub Release** — If repo is public
3. **Direct download link** — Dropbox, WeTransfer
4. **Email** — Only if <2GB (most email has 25GB limit)
5. **USB Drive** — Physical transfer if network slow

### Recommended

Share via **OneDrive** or **Google Drive** with link + password:
- Link expires after 7 days
- Track who downloaded
- No email attachment size limits
- Easy to re-upload if needed

---

## Troubleshooting for Team Member

If they encounter issues:

1. **Check file exists**: Verify `TEAM_SETUP_GUIDE.md` in root
2. **Run QUICK_INSTALL**: Let automated script handle dependencies
3. **Check .env files**: Make sure both `.env` files are set up
4. **Verify all 4 services**: Check each terminal for errors
5. **Check http://localhost:3000**: Should see Researchly dashboard

If still broken → they should **send error message + which terminal** → you debug

---

## Final Checklist Before Sharing

- [ ] ZIP file created (size 1.5-2GB)
- [ ] ZIP tested — can extract without errors
- [ ] `.env` files are `.env.example` only (no secrets)
- [ ] Trained models included (1.3GB in ZIP)
- [ ] Documentation files readable (UTF-8)
- [ ] `.git` history included (for git log)
- [ ] Team member has Node.js + Python installed
- [ ] Team member knows to read `TEAM_SETUP_GUIDE.md` first
- [ ] ZIP shared via secure link (OneDrive/Google Drive)

**You're ready to share!** ✓

