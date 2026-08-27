import httpx, json

BASE = "http://127.0.0.1:8003"
results = []

def call(id_, feature, method, path, payload=None, params=None, timeout=90):
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

# --- Feature B: Topic Categorization ---
call("M3-01", "Topic Categorization (CS/ML abstract)", "POST", "/data/categorize", {
    "text": "This paper presents a deep convolutional neural network architecture for classifying medical images, achieving state-of-the-art accuracy on a benchmark dataset using transfer learning and data augmentation techniques.",
    "threshold": 0.2, "top_k": 5
})
call("M3-02", "Topic Categorization (business abstract)", "POST", "/data/categorize", {
    "text": "This study examines the impact of digital marketing strategies on small and medium enterprise growth, analyzing consumer behavior and brand loyalty through a survey of 300 business owners.",
    "threshold": 0.2, "top_k": 5
})
call("M3-03", "Topic Categorization (health abstract)", "POST", "/data/categorize", {
    "text": "This clinical study investigates the effectiveness of a new physiotherapy intervention for post-surgical knee rehabilitation in elderly patients, measuring recovery outcomes over a six month period.",
    "threshold": 0.2, "top_k": 5
})
call("M3-04", "Topic Categorization status", "GET", "/data/categorize/status")

# --- Feature C: Point-Wise Summarizer ---
LONG_TEXT = (
    "This paper presents a novel deep learning approach for detecting plant diseases from leaf images using "
    "convolutional neural networks. In recent years, agricultural productivity in Sri Lanka has been severely "
    "affected by crop diseases, resulting in significant economic losses for farmers. Existing manual inspection "
    "methods are time-consuming and require expert knowledge that is often unavailable in rural areas. This study "
    "proposes a mobile-based system that uses a fine-tuned ResNet50 architecture trained on a dataset of 15,000 "
    "labeled leaf images spanning 12 disease categories across three crops: rice, tomato, and banana. The "
    "methodology involves collecting images from local farms, applying data augmentation techniques such as "
    "rotation and color jittering, and training the model using transfer learning with an initial learning rate "
    "of 0.001. We evaluate the model against three baseline approaches: a traditional SVM classifier, a shallow "
    "CNN, and a pretrained VGG16 model. Results show that our approach achieves 94.2% classification accuracy, "
    "outperforming the SVM baseline by 18 percentage points and the shallow CNN by 9 percentage points. The "
    "F1-score across all disease categories averaged 0.91, with the lowest performing category being early "
    "blight in tomato leaves at 0.83 F1. However, the model struggles with images taken under poor lighting "
    "conditions, and further work is needed to improve robustness to real-world capture conditions. In "
    "conclusion, this study demonstrates that deep learning based leaf disease detection can be feasibly "
    "deployed on mobile devices to assist smallholder farmers, though future work should explore on-device "
    "quantization to reduce inference latency and expand the dataset to cover additional crop varieties."
)
call("M3-05", "Summarizer (standard length)", "POST", "/data/summarize", {"text": LONG_TEXT, "length": "standard"})
call("M3-06", "Summarizer (quick length)", "POST", "/data/summarize", {"text": LONG_TEXT, "length": "quick"})
call("M3-07", "Summarizer (extensive length)", "POST", "/data/summarize", {"text": LONG_TEXT, "length": "extensive"})
call("M3-08", "Summarizer status", "GET", "/data/summarize/status")

# --- Feature D: Plagiarism Trend Analysis ---
call("M3-09", "Plagiarism Trend Search (topic)", "POST", "/data/plagiarism-trends/search", {
    "topic": "machine learning crop disease detection", "top_k": 5, "min_topic_similarity": 0.15
}, timeout=60)
call("M3-10", "Plagiarism Trends legacy (Supabase/fallback)", "GET", "/data/plagiarism-trends", params={"year_from": 2018, "year_to": 2026}, timeout=60)
call("M3-11", "Plagiarism Compare (near-identical text)", "POST", "/data/plagiarism-trends/compare", {
    "text_a": LONG_TEXT,
    "text_b": LONG_TEXT.replace("Sri Lanka", "Bangladesh").replace("ResNet50", "EfficientNet"),
    "title_a": "Original", "title_b": "Slightly modified copy",
})
call("M3-12", "Plagiarism Compare (unrelated texts)", "POST", "/data/plagiarism-trends/compare", {
    "text_a": LONG_TEXT,
    "text_b": "The stock market experienced significant volatility this quarter due to rising interest rates and geopolitical tensions affecting global supply chains. Investors are increasingly turning to diversified portfolios including bonds, real estate, and commodities to hedge against inflation risk in an uncertain macroeconomic environment.",
    "title_a": "Plant disease paper", "title_b": "Unrelated finance text",
})
call("M3-13", "Plagiarism Trends status", "GET", "/data/plagiarism-trends/status")

# --- Feature E: Data Quality ---
call("M3-14", "Data Quality Metrics", "GET", "/data/quality", timeout=30)

with open("_results_module3.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print("\nDone. Wrote _results_module3.json")
