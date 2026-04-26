#!/bin/bash
# Direct API Testing for Local Trained Models
# Test Citation NER and SBERT without using frontend

set -e

API_URL="http://localhost:3000/api/v1"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  LOCAL TRAINED MODELS API TEST                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ─── Test 1: Health Check ───────────────────────────────────────────────
echo "[1/4] Testing Health Endpoint..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HEALTH=$(curl -s "$API_URL/ai/local/health")
echo "Response:"
echo "$HEALTH" | python -m json.tool 2>/dev/null || echo "$HEALTH"

# Extract status
AVAILABLE=$(echo "$HEALTH" | python -c "import sys, json; print(json.load(sys.stdin)['available'])" 2>/dev/null || echo "error")
echo ""
if [ "$AVAILABLE" = "True" ] || [ "$AVAILABLE" = "true" ]; then
    echo "[✓] Status: Models available (AVAILABLE=true)"
else
    echo "[!] Status: Models NOT available (AVAILABLE=false)"
    echo "    Start paper-chat service: cd services/paper-chat && uvicorn app.main:app --reload --port 8005"
fi
echo ""

# ─── Test 2: Citation NER ───────────────────────────────────────────────
echo "[2/4] Testing Citation NER Model..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CITATION="Smith, J., Doe, A. (2023). Deep Learning for NLP. Journal of AI Research, 45(2), 123-145. doi:10.1234/jair.2023"

echo "Citation to parse:"
echo "  $CITATION"
echo ""
echo "Making request to local chat endpoint..."

RESPONSE=$(curl -s -X POST "$API_URL/ai/local/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "integrity",
    "message": "Extract citation components from: Smith, J., Doe, A. (2023). Deep Learning for NLP. Journal of AI Research, 45(2), 123-145. doi:10.1234/jair.2023",
    "context": null
  }')

echo "Response:"
echo "$RESPONSE"
echo ""

# ─── Test 3: SBERT Plagiarism ───────────────────────────────────────────
echo "[3/4] Testing SBERT Plagiarism Model..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEXT1="This paper proposes a deep neural network for sentiment analysis using transformer-based architectures."
TEXT2="We introduce a transformer neural network with attention mechanisms for sentiment classification in social media."

echo "Text 1: $TEXT1"
echo ""
echo "Text 2: $TEXT2"
echo ""
echo "Making request to local chat endpoint..."

RESPONSE=$(curl -s -X POST "$API_URL/ai/local/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"mode\": \"integrity\",
    \"message\": \"Check similarity/plagiarism between these texts. Text 1: $TEXT1 Text 2: $TEXT2\",
    \"context\": null
  }")

echo "Response:"
echo "$RESPONSE"
echo ""

# ─── Test 4: Check Response Time ───────────────────────────────────────
echo "[4/4] Checking Response Times..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing Citation NER latency..."
START=$(date +%s%N)
curl -s -X POST "$API_URL/ai/local/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "integrity",
    "message": "Parse: Vaswani, A., et al. (2017). Attention is all you need.",
    "context": null
  }' > /dev/null
END=$(date +%s%N)
LATENCY=$((($END - $START) / 1000000))

echo "Citation NER latency: ${LATENCY}ms"
if [ $LATENCY -lt 2000 ]; then
    echo "[✓] Fast response (< 2s)"
else
    echo "[!] Slow response (> 2s) - Check if models are loaded"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TEST COMPLETE                                                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  ✓ Health endpoint tested"
echo "  ✓ Citation NER tested"
echo "  ✓ SBERT Plagiarism tested"
echo "  ✓ Response times measured"
echo ""
echo "If tests passed: Local models are working! ✓"
echo "If tests failed: Check if paper-chat service is running."
echo ""
