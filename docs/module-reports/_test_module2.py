import httpx, json

BASE = "http://127.0.0.1:8002"
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

# --- Feature A: Supervisor Matching ---
call("M2-01", "Supervisor Matching (AI/ML proposal)", "POST", "/matching/supervisors", {
    "proposal": "A deep learning based system using convolutional neural networks for detecting plant diseases from leaf images, deployed as a mobile application for farmers.",
    "top_k": 5, "min_similarity": 0.1
})
call("M2-02", "Supervisor Matching (cybersecurity proposal)", "POST", "/matching/supervisors", {
    "proposal": "A network intrusion detection system using machine learning to identify cyberattacks in real time on enterprise networks.",
    "top_k": 5, "min_similarity": 0.1
})
call("M2-03", "Supervisor Matching (legacy interests+abstract format)", "POST", "/matching/supervisors", {
    "research_interests": ["natural language processing", "sentiment analysis"],
    "abstract": "Analyzing customer reviews using NLP techniques to extract sentiment and actionable insights for businesses.",
    "top_k": 5
})
call("M2-04", "Supervisor Matching (empty proposal)", "POST", "/matching/supervisors", {
    "proposal": "", "top_k": 5
})

# --- Feature B: Supervisor Profile Enrichment (live Semantic Scholar + Gemini) ---
call("M2-05", "Supervisor Papers/Profile (id=1)", "GET", "/matching/supervisors/1/papers", timeout=45)
call("M2-06", "Supervisor Papers/Profile (id=2)", "GET", "/matching/supervisors/2/papers", timeout=45)
call("M2-07", "Supervisor Papers/Profile (invalid id)", "GET", "/matching/supervisors/999999/papers", timeout=20)

# --- Feature C: Peer Connect (read-only) ---
# NOTE: app/routers/peer.py's own docstring says "/peers/groups" but main.py actually
# mounts this router with prefix="/matching" -> real path is /matching/groups. Verified bug.
call("M2-08", "Peer Groups List (open)", "GET", "/matching/groups", params={"status": "open"})
call("M2-09", "Peer Groups List (all)", "GET", "/matching/groups", params={"status": "all"})

# --- Feature D: Feedback & Aspect-Based Sentiment (analysis only, no DB write) ---
call("M2-10", "Sentiment Analysis (positive feedback)", "POST", "/feedback/analyze", {
    "feedback_text": "My supervisor was excellent throughout the project. The methodology guidance was clear and detailed, the writing feedback helped me improve a lot, and the originality of my idea was strongly encouraged. Data analysis support was outstanding."
}, timeout=30)
call("M2-11", "Sentiment Analysis (negative feedback)", "POST", "/feedback/analyze", {
    "feedback_text": "The supervisor rarely responded to emails. Methodology guidance was vague and unhelpful, the writing feedback was minimal, and originality was never discussed. Data analysis support was completely absent."
}, timeout=30)
call("M2-12", "Sentiment Analysis (mixed feedback)", "POST", "/feedback/analyze", {
    "feedback_text": "The methodology feedback was very thorough and helped shape the research design well. However, the writing feedback was quite sparse and originality was rarely discussed. Data analysis support was okay, nothing special."
}, timeout=30)
call("M2-13", "Rateable Supervisors Directory", "GET", "/feedback/supervisors")

# --- Feature E: Supervisor Effectiveness ---
call("M2-14", "Effectiveness List (all supervisors)", "GET", "/effectiveness", params={"limit": 30}, timeout=30)

with open("_results_module2.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print("\nDone. Wrote _results_module2.json")
