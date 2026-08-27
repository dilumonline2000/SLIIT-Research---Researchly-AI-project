import httpx, json

BASE = "http://127.0.0.1:8004"
results = []

def call(id_, feature, method, path, payload=None, params=None, timeout=60):
    try:
        with httpx.Client(timeout=timeout) as c:
            if method == "GET":
                r = c.get(BASE + path, params=params)
            else:
                r = c.post(BASE + path, json=payload)
        results.append({
            "id": id_, "feature": feature, "method": method, "path": path,
            "request": payload or params, "status": r.status_code,
            "response": r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:500],
        })
        print(f"[{id_}] {method} {path} -> {r.status_code}")
    except Exception as e:
        results.append({"id": id_, "feature": feature, "method": method, "path": path,
                         "request": payload or params, "status": "ERROR", "response": str(e)})
        print(f"[{id_}] {method} {path} -> ERROR: {e}")

# NOTE: main.py mounts every router in this service under prefix="/analytics"
# (trends/quality/dashboard/mindmap/prediction/papers all share it) -> verified by reading main.py.

# --- Feature A: Trend Forecasting ---
call("M4-01", "Trend Forecast (all topics, horizon=3)", "GET", "/analytics/trends", params={"horizon": 3}, timeout=30)
call("M4-02", "Trend Forecast (specific topic)", "GET", "/analytics/trends", params={"topic": "computing", "horizon": 5}, timeout=30)
call("M4-03", "Trend Compare (multi-topic)", "POST", "/analytics/trends/compare", {
    "topics": ["computing", "health", "business"], "horizon": 3
}, timeout=30)
call("M4-04", "Trend Insights (emerging topics)", "GET", "/analytics/trends/insights", params={"horizon": 3, "top_k": 5}, timeout=30)
call("M4-05", "Available Topics List", "GET", "/analytics/trends/topics")

# --- Feature B: Quality Scoring ---
STRONG_ABSTRACT = (
    "This paper proposes a novel convolutional neural network architecture for detecting plant diseases from "
    "leaf images. We evaluate our approach against three baseline methods including SVM and VGG16 on a dataset "
    "of 15,000 labeled images. Experimental results demonstrate that our proposed method achieves 94.2% "
    "classification accuracy, outperforming the SVM baseline by 18 percentage points [1]. Our methodology "
    "follows a systematic experimental design combining transfer learning with data augmentation. As shown in "
    "prior work (Smith et al., 2020), robustness under varying lighting conditions remains a challenge, which "
    "we address through cross-validation and a novel regularization scheme."
)
WEAK_TEXT = (
    "Employee Leave Request Form. Name: _____. Department: _____. Date of leave requested: from ___ to ___. "
    "Reason for leave: _____. Approved by supervisor: Yes / No. Please submit this form to HR at least two "
    "weeks in advance. Contact HR for any questions regarding company leave policy."
)
call("M4-06", "Quality Score (strong technical abstract)", "POST", "/analytics/quality-score", {
    "title": "Deep Learning for Plant Disease Detection", "abstract": STRONG_ABSTRACT
}, timeout=30)
call("M4-07", "Quality Score (generic non-research text)", "POST", "/analytics/quality-score", {
    "title": "Leave Request Form", "abstract": WEAK_TEXT
}, timeout=30)
call("M4-08", "Quality Score (missing input)", "POST", "/analytics/quality-score", {}, timeout=15)

# --- Feature C: Success Prediction ---
call("M4-09", "Success Prediction (strong abstract)", "POST", "/analytics/predict", {
    "title": "Deep Learning for Plant Disease Detection", "abstract": STRONG_ABSTRACT,
    "authors": ["A. Perera", "B. Silva"], "year": 2026
}, timeout=30)
call("M4-10", "Success Prediction (weak/generic text)", "POST", "/analytics/predict", {
    "title": "Leave Request Form", "abstract": WEAK_TEXT
}, timeout=30)
call("M4-11", "Success Prediction (short abstract, should reject)", "POST", "/analytics/predict", {
    "title": "Test", "abstract": "Too short"
}, timeout=15)

# --- Feature D: Concept Mind Maps ---
call("M4-12", "Mind Map (topic-based)", "POST", "/analytics/mindmap", {
    "topic": "machine learning for plant disease detection", "max_nodes": 20
}, timeout=45)
call("M4-13", "Mind Map (department-based)", "POST", "/analytics/mindmap", {
    "department": "Computer Science", "max_nodes": 15
}, timeout=45)

# --- Feature E: Cross-Module Dashboard ---
call("M4-14", "Cross-Module Dashboard KPIs", "GET", "/analytics/dashboard", timeout=30)

# --- Health/model info (real training metrics) ---
call("M4-15", "Health + model metadata (training metrics)", "GET", "/health")

with open("_results_module4.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print("\nDone. Wrote _results_module4.json")
