"""End-to-end smoke test hitting every gateway route.

Usage:
    python scripts/smoke_test.py [--gateway http://localhost:3001] [--email x@y.z] [--password secret]

Requirements:
    - api-gateway running on GATEWAY_URL
    - All 4 ML services running on 8001-8004 (or GATEWAY will return 502)
    - A test user in Supabase (use --email / --password, defaults to env SMOKE_TEST_EMAIL/PASSWORD)

Exit code is the number of failing tests.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import requests

# ANSI color codes — fall back to blank on Windows cmd without ansicon
RED = "\033[31m" if sys.stdout.isatty() else ""
GREEN = "\033[32m" if sys.stdout.isatty() else ""
YELLOW = "\033[33m" if sys.stdout.isatty() else ""
RESET = "\033[0m" if sys.stdout.isatty() else ""


@dataclass
class TestCase:
    name: str
    method: str
    path: str
    body: dict | None = None
    expected_status: int = 200
    expected_keys: list[str] = field(default_factory=list)
    requires_auth: bool = True
    skip_reason: str | None = None


@dataclass
class Result:
    case: TestCase
    passed: bool
    status: int | None = None
    error: str | None = None
    response_snippet: str | None = None


def build_test_cases() -> list[TestCase]:
    """Every endpoint we want to exercise, in dependency order."""
    return [
        # --- Health ---
        TestCase(name="gateway health", method="GET", path="/api/v1/health",
                 requires_auth=False, expected_keys=["status"]),

        # --- Module 1: Integrity ---
        TestCase(name="m1 citation parse", method="POST", path="/api/v1/citations/parse",
                 body={"raw_text": "Smith J, Doe A. Deep Learning for NLP. Nature. 2024;12(3):45-67."},
                 expected_keys=["parsed", "confidence"]),
        TestCase(name="m1 citation format", method="POST", path="/api/v1/citations/format",
                 body={"parsed": {"authors": ["Smith J", "Doe A"], "title": "Deep Learning for NLP",
                                   "journal": "Nature", "year": 2024, "volume": "12", "issue": "3",
                                   "pages": "45-67"}, "style": "apa"},
                 expected_keys=["formatted"]),
        TestCase(name="m1 gap analysis", method="POST", path="/api/v1/gaps/analyze",
                 body={"topic": "federated learning for healthcare", "corpus_size": 20},
                 expected_keys=["gaps"]),
        TestCase(name="m1 proposal generate", method="POST", path="/api/v1/proposals/generate",
                 body={"topic": "graph neural networks for drug discovery", "domain": "ml",
                       "gap": "limited benchmarks"},
                 expected_keys=["proposal"]),
        TestCase(name="m1 plagiarism check", method="POST", path="/api/v1/plagiarism/check",
                 body={"text": "Transformers have revolutionized NLP with self-attention mechanisms.",
                       "threshold": 0.75},
                 expected_keys=["overall_similarity", "risk_level"]),
        TestCase(name="m1 mindmap generate", method="POST", path="/api/v1/mindmaps/generate",
                 body={"text": "Reinforcement learning uses reward signals to train agents."},
                 expected_keys=["nodes"]),

        # --- Module 2: Collaboration ---
        TestCase(name="m2 supervisor match", method="POST", path="/api/v1/matching/supervisors",
                 body={"student_id": "smoke-test-student",
                       "research_interests": ["machine learning", "nlp"],
                       "abstract": "A study on transformer efficiency.", "top_k": 5},
                 expected_keys=["matches"]),
        TestCase(name="m2 peer match", method="POST", path="/api/v1/matching/peers",
                 body={"user_id": "smoke-test-user", "top_k": 5},
                 expected_keys=["matches"]),
        TestCase(name="m2 feedback analyze", method="POST", path="/api/v1/feedback/analyze",
                 body={"text": "The methodology is weak but the writing is clear and well-structured."},
                 expected_keys=["aspects"]),
        TestCase(name="m2 effectiveness", method="GET",
                 path="/api/v1/effectiveness/smoke-test-supervisor",
                 expected_keys=["supervisor_id", "overall_score"]),

        # --- Module 3: Data ---
        TestCase(name="m3 categorize", method="POST", path="/api/v1/data/categorize",
                 body={"text": "We propose a novel transformer architecture for image classification."},
                 expected_keys=["categories"]),
        TestCase(name="m3 plagiarism trends", method="GET",
                 path="/api/v1/data/plagiarism-trends?year_from=2020&year_to=2026",
                 expected_keys=["trends"]),
        TestCase(name="m3 summarize", method="POST", path="/api/v1/data/summarize",
                 body={"text": "Deep learning has transformed many fields of AI. "
                               "Transformers in particular have become the dominant architecture. "
                               "They excel at sequence modeling tasks across language and vision.",
                       "length": "short"},
                 expected_keys=["summary"]),
        TestCase(name="m3 quality", method="GET", path="/api/v1/data/quality",
                 expected_keys=["total_papers"]),

        # --- Module 4: Analytics ---
        TestCase(name="m4 trends", method="GET", path="/api/v1/analytics/trends?horizon=6",
                 expected_keys=["forecasts"]),
        TestCase(name="m4 quality score", method="POST", path="/api/v1/analytics/quality-score",
                 body={"proposal_id": "smoke-test-proposal", "user_id": "smoke-test-user"},
                 expected_keys=["overall_score"]),
        TestCase(name="m4 dashboard", method="GET", path="/api/v1/analytics/dashboard",
                 expected_keys=["total_proposals", "avg_quality_score"]),
        TestCase(name="m4 mindmap", method="POST", path="/api/v1/analytics/mindmap",
                 body={"topic": "quantum computing", "max_nodes": 20},
                 expected_keys=["nodes", "edges"]),
        TestCase(name="m4 predict", method="POST", path="/api/v1/analytics/predict",
                 body={"proposal_id": "smoke-test-proposal", "user_id": "smoke-test-user"},
                 expected_keys=["success_probability", "risk_level"]),
    ]


def login(email: str, password: str) -> str | None:
    """Authenticate against Supabase Auth directly and return the JWT.

    Reads SUPABASE_URL and SUPABASE_ANON_KEY from env (or .env via python-dotenv if available).
    """
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except ImportError:
        pass

    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not supabase_url or not anon_key:
        print(f"{RED}SUPABASE_URL / SUPABASE_ANON_KEY not set in env — cannot authenticate.{RESET}")
        return None

    try:
        r = requests.post(
            f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password",
            headers={"apikey": anon_key, "Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=15,
        )
    except Exception as e:
        print(f"{RED}Supabase auth request failed: {e}{RESET}")
        return None

    if r.status_code != 200:
        print(f"{RED}Supabase login failed ({r.status_code}): {r.text[:200]}{RESET}")
        return None
    return r.json().get("access_token")


def run_case(gateway: str, case: TestCase, token: str | None) -> Result:
    if case.skip_reason:
        return Result(case=case, passed=True, error=f"SKIP: {case.skip_reason}")

    url = f"{gateway}{case.path}"
    headers = {"Content-Type": "application/json"}
    if case.requires_auth and token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if case.method == "GET":
            r = requests.get(url, headers=headers, timeout=90)
        else:
            r = requests.post(url, headers=headers, json=case.body, timeout=90)
    except requests.exceptions.RequestException as e:
        return Result(case=case, passed=False, error=f"request exception: {e}")

    snippet = r.text[:250]

    if r.status_code != case.expected_status:
        return Result(
            case=case, passed=False, status=r.status_code,
            error=f"expected {case.expected_status}, got {r.status_code}",
            response_snippet=snippet,
        )

    # Body shape check
    try:
        body = r.json()
    except ValueError:
        return Result(case=case, passed=False, status=r.status_code,
                      error="response is not valid JSON", response_snippet=snippet)

    missing = [k for k in case.expected_keys if k not in body]
    if missing:
        return Result(case=case, passed=False, status=r.status_code,
                      error=f"missing keys: {missing}", response_snippet=snippet)

    return Result(case=case, passed=True, status=r.status_code, response_snippet=snippet)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gateway smoke test")
    parser.add_argument("--gateway", default=os.environ.get("GATEWAY_URL", "http://localhost:3001"))
    parser.add_argument("--email", default=os.environ.get("SMOKE_TEST_EMAIL", "smoketest@researchly.local"))
    parser.add_argument("--password", default=os.environ.get("SMOKE_TEST_PASSWORD", "SmokeTest!2026"))
    parser.add_argument("--no-auth", action="store_true", help="Skip login; send unauthed requests")
    parser.add_argument("--filter", default=None, help="Only run cases whose name contains this substring")
    args = parser.parse_args()

    gateway = args.gateway.rstrip("/")
    print(f"\n{YELLOW}═══ Smoke test against {gateway} ═══{RESET}\n")

    # Login
    token: str | None = None
    if not args.no_auth:
        print(f"Logging in as {args.email}…")
        token = login(args.email, args.password)
        if not token:
            print(f"{YELLOW}No token — protected routes will fail. "
                  f"Create the user first or pass --no-auth.{RESET}\n")
        else:
            print(f"{GREEN}✓ got token{RESET}\n")

    cases = build_test_cases()
    if args.filter:
        cases = [c for c in cases if args.filter.lower() in c.name.lower()]

    results: list[Result] = []
    for case in cases:
        t0 = time.time()
        res = run_case(gateway, case, token)
        dt_ms = int((time.time() - t0) * 1000)
        mark = f"{GREEN}✓{RESET}" if res.passed else f"{RED}✗{RESET}"
        status = f"[{res.status}]" if res.status else "[---]"
        print(f"  {mark} {status} {dt_ms:>5}ms  {case.name}")
        if not res.passed and res.error:
            print(f"      {RED}{res.error}{RESET}")
            if res.response_snippet:
                print(f"      {res.response_snippet}")
        results.append(res)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    print(f"\n{YELLOW}═══ {passed} passed, {failed} failed ═══{RESET}\n")
    return failed


if __name__ == "__main__":
    sys.exit(main())
