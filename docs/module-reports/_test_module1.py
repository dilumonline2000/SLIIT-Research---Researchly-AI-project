import httpx, json, sys

BASE = "http://127.0.0.1:8001"
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

# --- Feature A: Citation Parser & Formatter ---
call("M1-01", "Citation Parser", "POST", "/citations/parse", {
    "raw_text": "Perera, K. and Silva, M. (2021). Deep learning for crop disease detection in Sri Lanka. Journal of Agricultural Informatics, 12(3), 45-58."
})
call("M1-02", "Citation Parser", "POST", "/citations/parse", {
    "raw_text": "J. Fernando, S. Bandara and A. Kumar, \"IoT-based smart irrigation system,\" in Proc. IEEE Int'l Conf. on Smart Computing, 2020, pp. 112-119."
})
call("M1-03", "Citation Parser (incomplete input)", "POST", "/citations/parse", {
    "raw_text": "Some paper about machine learning without proper structure"
})
call("M1-04", "Citation Formatter", "POST", "/citations/format", {
    "parsed": {
        "raw": "", "source_type": "journal", "authors": ["Perera, K.", "Silva, M."],
        "title": "Deep learning for crop disease detection in Sri Lanka",
        "year": 2021, "journal": "Journal of Agricultural Informatics",
        "volume": "12", "issue": "3", "pages": "45-58", "doi": "10.1234/jai.2021.0012"
    },
    "style": "ieee"
})
call("M1-05", "DOI Lookup (CrossRef, real DOI)", "POST", "/citations/lookup-doi", {"doi": "10.1038/nphys1170"})
call("M1-06", "Similar Papers (SBERT retrieval)", "POST", "/citations/similar-papers", {
    "query": "machine learning for early detection of plant diseases", "top_k": 5
})
call("M1-07", "Reference List (APA, sorting)", "POST", "/citations/reference-list", {
    "entries": [
        {"raw":"","source_type":"journal","authors":["Zhang, Y."],"title":"Zebra paper","year":2019,"journal":"J. X"},
        {"raw":"","source_type":"journal","authors":["Amir, A."],"title":"Alpha paper","year":2020,"journal":"J. Y"},
    ],
    "style": "apa"
})

# --- Feature B: Research Gap Analysis ---
call("M1-08", "Gap Analysis", "POST", "/gaps/analyze", {
    "topic": "machine learning for crop disease detection in Sri Lanka", "top_k": 6, "min_similarity": 0.15
}, timeout=90)
call("M1-09", "Gap Analysis (obscure topic)", "POST", "/gaps/analyze", {
    "topic": "quantum cryptography for underwater acoustic sensor networks", "top_k": 6, "min_similarity": 0.15
}, timeout=90)
call("M1-10", "Gap Analysis status", "GET", "/gaps/status")

# --- Feature C: Proposal Generator ---
call("M1-11", "Proposal Generation", "POST", "/proposals/generate", {
    "topic": "IoT-based smart irrigation for paddy fields", "domain": "Agriculture Technology", "top_k": 5
}, timeout=90)
call("M1-12", "Proposal Generator status", "GET", "/proposals/status")

# --- Feature D: Plagiarism Checker ---
call("M1-13", "Plagiarism Check (likely novel text)", "POST", "/plagiarism/check", {
    "text": "This unique passage about the migratory habits of purple sea urchins in Antarctic waters was written specifically for this test and does not exist anywhere else.",
    "threshold": 0.8
}, timeout=60)
call("M1-14", "Plagiarism Check (generic ML sentence)", "POST", "/plagiarism/check", {
    "text": "Machine learning models such as convolutional neural networks have been widely used for image classification tasks in recent research, achieving high accuracy on benchmark datasets.",
    "threshold": 0.75
}, timeout=60)

# --- Feature E: Mind Map Builder ---
call("M1-15", "Mind Map Generation", "POST", "/mindmaps/generate", {
    "text": "This study investigates the use of deep learning, specifically convolutional neural networks, for detecting plant diseases from leaf images. The methodology involves collecting a dataset of diseased and healthy leaves, training a CNN model, and evaluating its accuracy against baseline methods. Results show significant improvement over traditional image processing techniques. Future work should explore mobile deployment for farmers in rural areas.",
    "max_nodes": 15
}, timeout=60)

with open("_results_module1.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print("\nDone. Wrote _results_module1.json")
