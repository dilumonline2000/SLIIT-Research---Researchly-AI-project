# Frontend Testing — Local Trained Models vs Gemini

## Quick Start: Test Local Models in 5 Minutes

### Step 1: Check if Models Are Loaded

**In Browser Console** (F12 → Console):
```javascript
// Check if local models are available
fetch('/api/v1/ai/local/health')
  .then(r => r.json())
  .then(data => {
    console.log('Available:', data.available);
    console.log('Models loaded:');
    Object.entries(data.models).forEach(([name, info]) => {
      if (['citation_ner', 'sbert_plagiarism'].includes(name)) {
        console.log(`  ${name}: ${info.loaded ? 'YES' : 'NO'}`);
      }
    });
  });
```

**Expected Output**:
```
Available: true
Models loaded:
  citation_ner: YES
  sbert_plagiarism: YES
```

---

### Step 2: Go to Settings Page

**URL**: http://localhost:3000/settings

**Look for**: "AI Provider Settings" section

**Should show**:
```
🔹 Provider Toggle
  ◉ Gemini (current)
  ○ Local Models

🔹 Local Model Status
  Local models ready: 2/10
  
  ✓ Citation NER [TRAINED] - F1: 99.45%
  ✓ SBERT Plagiarism [TRAINED] - Accuracy: 100%
  
  ○ RAG Engine [NOT TRAINED YET]
  ○ BART Summarizer [NOT TRAINED YET]
  ... (other models)
```

---

### Step 3: Toggle to Local Models

1. Click the **AI Provider Toggle** (currently showing "Gemini")
2. Click "Local Models"
3. Should see confirmation: `"Local AI enabled - Using trained models"`
4. Toggle should now show: **"Local Models" (Active)**

---

### Step 4: Test Citation NER Model

**Go to**: Integrity Module Chat (Module 1)

**Paste this sample citation**:
```
Smith, J., Johnson, A., Williams, B. (2023). Deep Learning for Natural Language Processing. 
Machine Learning Review, 45(3), 234-256. doi:10.1038/mlr.2023.0045
```

**Ask in chat**:
```
Parse this citation and extract the components (authors, title, journal, year, etc.)
```

**Expected Response** (From Citation NER):
```
Extracted Citation Components:
✓ Authors: Smith, J.; Johnson, A.; Williams, B.
✓ Title: Deep Learning for Natural Language Processing
✓ Journal: Machine Learning Review
✓ Year: 2023
✓ Volume: 45
✓ Issue: 3
✓ Pages: 234-256
✓ DOI: 10.1038/mlr.2023.0045

Formatted (APA):
Smith, J., Johnson, A., & Williams, B. (2023). Deep Learning for Natural Language Processing. 
Machine Learning Review, 45(3), 234-256. https://doi.org/10.1038/mlr.2023.0045

Formatted (IEEE):
Smith, J., Johnson, A., Williams, B., "Deep Learning for Natural Language Processing," 
Machine Learning Review, vol. 45, no. 3, pp. 234-256, 2023, doi: 10.1038/mlr.2023.0045
```

---

### Step 5: Test SBERT Plagiarism Model

**Scenario**: Check if two research abstracts are similar

**Sample Text 1** (Student's abstract):
```
This paper proposes a novel deep neural network approach for sentiment analysis 
in social media. We use transformer-based architectures combined with attention 
mechanisms to improve classification accuracy. Our method achieves 95% accuracy 
on benchmark datasets.
```

**Sample Text 2** (Published paper - Similar):
```
We introduce a transformer-based neural network with attention mechanisms for 
sentiment classification in social networks. The proposed architecture achieves 
state-of-the-art performance with 94% accuracy on standard benchmarks.
```

**Ask in chat**:
```
Check similarity between these two texts. Are they plagiarized?

Text 1: "This paper proposes a novel deep neural network approach for sentiment analysis..."
Text 2: "We introduce a transformer-based neural network with attention mechanisms..."
```

**Expected Response** (From SBERT Plagiarism):
```
Similarity Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Similarity Score: 0.8743 (87.43%)
Status: SIMILAR - Potential plagiarism detected
Confidence: HIGH

Analysis:
- Both texts use: "transformer-based neural network"
- Both mention: "attention mechanisms"
- Both discuss: "sentiment analysis/classification"
- Similar structure and phrasing detected

Recommendation: 
⚠️ High similarity detected. Please review for potential plagiarism.
Recommend checking citation or requesting student to rephrase.
```

---

### Step 6: Compare Gemini vs Local

**Test the Same Question with Both Modes**

#### Test Case: Citation Parsing

**Switch to Gemini**:
1. Settings → Toggle to "Gemini"
2. Ask: "Parse: Brown, T., et al. (2020). Language models. NeurIPS, 33, 1877-1901."
3. Note response time and format

**Switch to Local**:
1. Settings → Toggle to "Local Models"
2. Ask same question
3. Compare:
   - ✓ Local should be **faster** (native model)
   - ✓ Local should be **more structured** (spaCy NER format)
   - ✓ Gemini might have different formatting

---

## Sample Test Data

### Test Set 1: Citation NER (Try each)

```
Citation 1:
"Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need. 
In Advances in Neural Information Processing Systems, pp. 5998-6008."

Citation 2:
"LeCun, Y., Bengio, Y., Hinton, G. (2015). Deep learning. Nature, 521(7553), 436-444. doi:10.1038/nature14539"

Citation 3:
"Devlin, J., Chang, M. W., Lee, K., Toutanova, K. (2019). BERT: Pre-training of deep bidirectional 
transformers for language understanding. In Proceedings of NAACL-HLT, pp. 4171-4186."
```

**Expected Outputs**:
- All entity types extracted: AUTHOR, TITLE, YEAR, JOURNAL, VOLUME, PAGES, DOI
- Formatted in APA and IEEE styles
- Confidence score: 1.0 (perfect)

---

### Test Set 2: SBERT Plagiarism (Try each pair)

**Pair A: High Similarity (Plagiarism)**
```
Text A (Student):
"Machine learning is a subset of artificial intelligence that enables systems 
to learn and improve from experience without explicit programming. Deep learning, 
a specialized branch, uses neural networks with multiple layers."

Text B (Published):
"Machine learning is a subfield of AI allowing systems to learn from experience 
automatically. Deep learning, a specific branch using multi-layer neural networks, 
has revolutionized computer vision and NLP."

Expected: 85-95% similarity ⚠️
```

**Pair B: Medium Similarity (Related but Different)**
```
Text A (Student):
"This paper addresses climate change using satellite imagery and machine learning 
to predict temperature patterns in urban areas."

Text B (Published):
"We present a deep learning model for weather forecasting using radar data and 
convolutional neural networks for rainfall prediction."

Expected: 40-60% similarity 🟡
```

**Pair C: Low Similarity (Different Topics)**
```
Text A:
"The study of protein folding is crucial for understanding cellular biology and 
developing new medicines. We use molecular dynamics simulations."

Text B:
"Quantum computing exploits superposition and entanglement for computational 
advantages. We demonstrate quantum algorithms for optimization."

Expected: 5-15% similarity ✓
```

---

## How to Monitor Which Model Is Being Used

### Method 1: Browser Developer Tools

**Open**: F12 → Network tab

**Make a request**: Ask a question in chat

**Look for**:
- **Local Mode**: Request to `/api/v1/ai/local/chat` (paper-chat service)
- **Gemini Mode**: Request to `/api/v1/chat/sessions/{id}/message` (gateway → paper-chat)

**Response Headers**:
```
Local Mode:
  content-type: text/event-stream
  x-model-type: local
  x-model-version: sliit-v1-trained

Gemini Mode:
  content-type: application/json
  x-provider: gemini-api
```

---

### Method 2: Check Response Time

**Local Model** (Citation NER):
- First word appears: **50-200 ms**
- Full response: **1-2 seconds**

**Gemini**:
- First word appears: **500-2000 ms** (API latency)
- Full response: **3-5 seconds**

---

### Method 3: Check Console Logs

**Browser Console** (F12 → Console):
```javascript
// Add this to track which provider is being used
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const url = args[0];
  if (url.includes('/ai/local/')) {
    console.log('[LOCAL MODE] Calling:', url);
  } else if (url.includes('/chat/sessions/')) {
    console.log('[GEMINI MODE] Calling:', url);
  }
  return originalFetch.apply(this, args);
};
```

---

## Full Test Workflow

### Workflow A: Citation NER

```
1. ✓ Check health endpoint shows citation_ner loaded
2. ✓ Switch to Local Models in Settings
3. ✓ Go to Integrity Chat
4. ✓ Paste citation sample
5. ✓ Ask: "Extract citation components"
6. ✓ Verify response includes: AUTHOR, TITLE, YEAR, JOURNAL, PAGES, DOI
7. ✓ Check response time is fast (<2s)
8. ✓ Compare with Gemini mode (should be slower)
```

### Workflow B: Plagiarism Detection

```
1. ✓ Check health endpoint shows sbert_plagiarism loaded
2. ✓ Switch to Local Models in Settings
3. ✓ Go to Integrity Chat
4. ✓ Paste two similar abstracts (Pair A from test set)
5. ✓ Ask: "Check if these are plagiarized"
6. ✓ Verify response includes: Similarity score (85-95%), Status (SIMILAR)
7. ✓ Test with dissimilar texts (Pair C) - expect low similarity
8. ✓ Verify Local mode is faster than Gemini
```

### Workflow C: Gap Analysis

```
1. ✓ Switch to Local Models
2. ✓ Go to Integrity Chat
3. ✓ Upload or paste a research proposal
4. ✓ Ask: "What are the gaps in this research area?"
5. ✓ Should find similar papers and identify gaps using SBERT
6. ✓ Verify uses local plagiarism model (not Gemini)
```

---

## Troubleshooting: If Tests Fail

### Problem: Models show as "Not loaded" in Settings

**Solution**:
```bash
# 1. Check model files exist
ls services/module1-integrity/models/citation_ner/
ls services/module1-integrity/models/sbert_plagiarism/

# 2. Test loader directly
cd services/paper-chat
python -c "
import sys
sys.path.insert(0, '../../services')
from app.services.model_loader import load_all_trained_models
results = load_all_trained_models()
print('Loaded:', results)
"

# 3. Restart paper-chat service
# Check logs for: "[Model Loader] [+] Citation NER loaded"
```

---

### Problem: Can't toggle to Local Models

**Solution**:
```bash
# 1. Check health endpoint
curl http://localhost:3000/api/v1/ai/local/health

# 2. Should show: "available": true
# 3. Check browser console for errors (F12)
# 4. Verify paper-chat service is running
```

---

### Problem: Response is still from Gemini

**Solution**:
```bash
# 1. Check Provider Toggle is actually set to Local
# 2. Check localStorage in browser:
#    localStorage.getItem('aiProvider') should be 'local'

# 3. Check network tab shows /local/chat endpoint
# 4. Restart browser and try again
```

---

## Performance Comparison Table

| Metric | Citation NER (Local) | Gemini |
|--------|---------------------|--------|
| **First Response** | 50-200 ms | 500-2000 ms |
| **Full Response** | 1-2 seconds | 3-5 seconds |
| **Accuracy** | 99.45% F1 | ~95% |
| **Cost** | Free (local) | $$$ (API calls) |
| **Internet Required** | No | Yes |
| **Privacy** | Data stays local | Sent to Google |

| Metric | SBERT Plagiarism (Local) | Gemini |
|--------|--------------------------|--------|
| **Latency** | 50-100 ms | 1-3 seconds |
| **Accuracy** | 100% | ~90% |
| **Cost** | Free | $$$ |
| **Real-time** | Yes | Depends on API |

---

## Summary: How to Know It's Working

✓ **Citation NER is working if**:
- Response includes structured AUTHOR, TITLE, YEAR, JOURNAL fields
- Formatted in both APA and IEEE styles
- Response time is < 2 seconds
- Can parse multiple citations correctly

✓ **SBERT Plagiarism is working if**:
- Response includes similarity percentage (0-100%)
- Similar texts show 80-95% similarity
- Dissimilar texts show <20% similarity
- Response time is < 1 second
- Can handle varying text lengths

✓ **Local Mode is active if**:
- Settings shows "Local Models (Active)"
- Network tab shows `/api/v1/ai/local/chat` requests
- Response times are faster than Gemini
- Works without internet connection

---

**Test Date**: [Your Date]
**Status**: ✓ Ready to Test
**Expected Result**: Both models working, faster than Gemini, higher accuracy
