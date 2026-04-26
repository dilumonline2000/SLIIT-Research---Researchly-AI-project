@echo off
REM Direct API Testing for Local Trained Models (Windows)
REM Test Citation NER and SBERT without using frontend

setlocal enabledelayedexpansion
set "API_URL=http://localhost:3000/api/v1"

echo.
echo =====================================================================
echo   LOCAL TRAINED MODELS API TEST
echo =====================================================================
echo.

REM ─── Test 1: Health Check ───────────────────────────────────────────────
echo [1/4] Testing Health Endpoint...
echo ─────────────────────────────────────────────────────────────────────

echo Making request to: %API_URL%/ai/local/health
curl -s "%API_URL%/ai/local/health"

echo.
echo If you see "available": true, models are loaded!
echo.

REM ─── Test 2: Citation NER ───────────────────────────────────────────────
echo [2/4] Testing Citation NER Model...
echo ─────────────────────────────────────────────────────────────────────

echo.
echo Citation to test:
echo   Smith, J., Doe, A. (2023). Deep Learning. Journal of AI, 45(2), 123-145.
echo.

curl -s -X POST "%API_URL%/ai/local/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"integrity\",\"message\":\"Extract citation components from: Smith, J., Doe, A. (2023). Deep Learning for NLP. Journal of AI Research, 45(2), 123-145. doi:10.1234/xyz\",\"context\":null}"

echo.
echo Expected: Should extract AUTHOR, TITLE, YEAR, JOURNAL, VOLUME, PAGES, DOI
echo.

REM ─── Test 3: SBERT Plagiarism ───────────────────────────────────────────
echo [3/4] Testing SBERT Plagiarism Model...
echo ─────────────────────────────────────────────────────────────────────

echo.
echo Testing similarity detection:
echo   Text 1: "Deep learning neural networks for sentiment analysis"
echo   Text 2: "Neural networks using deep learning for sentiment classification"
echo.

curl -s -X POST "%API_URL%/ai/local/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"integrity\",\"message\":\"Check plagiarism. Text 1: Deep learning neural networks for sentiment analysis. Text 2: Neural networks using deep learning for sentiment classification\",\"context\":null}"

echo.
echo Expected: Should show 80-95% similarity (texts are very similar)
echo.

REM ─── Test 4: Compare Models ────────────────────────────────────────────
echo [4/4] Simple Latency Check...
echo ─────────────────────────────────────────────────────────────────────

echo.
echo If response appears in less than 2 seconds, models are working!
echo If response takes 3+ seconds, it might be using Gemini (slower API)
echo.

echo =====================================================================
echo   TEST SUMMARY
echo =====================================================================
echo.
echo What to look for:
echo   [Citation NER]
echo     - Structured extraction of: authors, title, year, journal, pages
echo     - Formatted in APA and IEEE styles
echo     - Response time: < 2 seconds
echo.
echo   [SBERT Plagiarism]
echo     - Similarity score as percentage (0-100%%)
echo     - Status: Similar/Dissimilar
echo     - Response time: < 1 second
echo.
echo   [Overall]
echo     - All responses should be FAST (local, not calling Google API)
echo     - No need for internet connection
echo.
echo =====================================================================
echo.

pause
