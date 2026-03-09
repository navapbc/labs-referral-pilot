#!/usr/bin/env python3
"""
Retest queries from the QA Error Log to check if contact info and
description errors persist with the current production prompts + RAG data.

Uses reasoning_effort="none" (production default), production prompt versions,
and local ChromaDB populated with production knowledge base files.

Usage:
    python app/scripts/retest_qa_errors.py
"""

from __future__ import annotations

import csv
import json
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

API_BASE = "http://localhost:3000"
PHOENIX_BASE = "http://localhost:6006"
PHOENIX_PROJECT = "local-docker-project"

# Local Phoenix prompt version IDs matching production
PROMPT_VERSION_IDS = {
    "centraltx": "UHJvbXB0VmVyc2lvbjoxMg==",
    "keystone": "UHJvbXB0VmVyc2lvbjoxMw==",
}

# Each entry is a unique query from the QA error log (non-versioned, open errors).
# error_rows: which QA Error Log Row(s) reference this query
# errors_to_check: the specific resources/issues to look for in the response
RETEST_PROMPTS = [
    {
        "label": "row5-shower-restrooms",
        "error_rows": ["5"],
        "suffix": "centraltx",
        "query": "shower/restrooms information for homeless client",
        "errors_to_check": [
            "Goodwill Keystone Area - wrong phone (717-232-1831 is HQ not Reading)",
            "Goodwill Keystone Area - 3001 St. Lawrence Ave is Outlet Center not career services",
            "United Way of Berks County - wrong address (631 Penn St vs 25 N 2nd St Suite 101)",
            "BCAP - wrong URL (berkscap.org vs bcapberks.org)",
        ],
    },
    {
        "label": "row7-food-pantries",
        "error_rows": ["7"],
        "suffix": "centraltx",
        "query": (
            "My client is looking for food pantries that can give her "
            "groceries or a hot meal"
        ),
        "errors_to_check": [
            "Mission Possible B.A.G.S. - should mention 'at capacity' status",
        ],
    },
    {
        "label": "row11-day-shelters",
        "error_rows": ["11"],
        "suffix": "centraltx",
        "query": "Daytime Only shelters for homeless people in austin",
        "errors_to_check": [
            "Bucks County Human Services Hub - wrong phone (215-348-6000 is courthouse)",
        ],
    },
    {
        "label": "row16-warming-centers",
        "error_rows": ["16"],
        "suffix": "centraltx",
        "query": "day warming centers for homeless populations",
        "errors_to_check": [
            "SSA - online tool doesn't work for children SSN replacement",
        ],
    },
    {
        "label": "row25-cold-weather",
        "error_rows": ["25"],
        "suffix": "centraltx",
        "query": "Cap metro cold weather information",
        "errors_to_check": [
            "Starkey Hearing Foundation - wrong address (6801 vs 6700 Washington Ave S)",
            "WilCo Care - doesn't cover hearing aids (covers medical/dental/vision only)",
        ],
    },
    {
        "label": "row122-food-pantries-78753",
        "error_rows": ["122"],
        "suffix": "centraltx",
        "query": (
            "My client is looking for food pantries open today to get "
            "groceries or a hot meal.\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX 78753"
        ),
        "errors_to_check": [
            "Manos de Cristo - missing phone (512) 628-4199",
            "Gethsemane Lutheran Church - missing phone (512) 836-8560",
            "Society of St. Vincent de Paul - missing phone 512-251-6995",
            "Travis County CC Manor/Oak Hill - poor proximity (~20mi from 78753)",
        ],
    },
    {
        "label": "row133-GED-south-austin",
        "error_rows": ["133"],
        "suffix": "centraltx",
        "query": (
            "My client is seeking to get his GED in south austin texas, at no cost."
        ),
        "errors_to_check": [
            "Travis County Jobs - broken URL (/hrm/jobs vs /human-resources/jobs)",
        ],
    },
    {
        "label": "row141-food-transport",
        "error_rows": ["141"],
        "suffix": "centraltx",
        "query": (
            "Client is seeking food and transportation assistance visa cards "
            "or financial monetary\n"
            "Include resources that support the following categories: "
            "Housing & Shelter, Food Assistance, Transportation\n"
            "Include the following types of providers: community\n"
            "Focus on resources close to the following location: 75753"
        ),
        "errors_to_check": [
            "CPR Certification Austin - wrong address (3430 W William Cannon vs 701 Tillery)",
        ],
    },
    {
        "label": "row145-veteran-dui",
        "error_rows": ["146"],
        "suffix": "centraltx",
        "query": (
            "Client is a veteran who needs legal assistance for a recent DUI, "
            "financial assistance for rent, groceries, and bills, and assistance "
            "in appealing a disability rating decision with the Department of "
            "Veterans Affairs. Client lives in Travis county, is currently "
            "unemployed but is receiving VA disability in the amount of approx. "
            "$3800 per month, exceeding some income eligibility requirements.\n"
            "Include resources that support the following categories: "
            "Employment & Job Training, Food Assistance, Transportation, "
            "Financial Assistance, Legal Services, Veterans Services\n"
            "Include the following types of providers: goodwill, government, community\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX 78704"
        ),
        "errors_to_check": [
            "City of Austin Day Labor - wrong address (2514 Sol Wilson vs 700 E 7th)",
            "City of Austin Day Labor - wrong phone (512-974-1730 vs 512-972-4100)",
        ],
    },
    {
        "label": "row149-veteran-homeless",
        "error_rows": ["149"],
        "suffix": "centraltx",
        "query": (
            "My client is a veteran who is homeless and unemployed. He is currently "
            "living out of his truck. He is on the waitlist for HUD VASH.\n"
            "Include resources that support the following categories: "
            "Employment & Job Training, Housing & Shelter, Financial Assistance, "
            "Veterans Services\n"
            "Include the following types of providers: government, community\n"
            "Focus on resources close to the following location: Pflugerville, Texas"
        ),
        "errors_to_check": [
            "St. Vincent de Paul Austin - broken URL (austinsvdp.info/locate-assistance/ is 404)",
        ],
    },
    {
        "label": "row216-background-friendly",
        "error_rows": ["216"],
        "suffix": "centraltx",
        "query": "background friendly employers in north Austin texas.",
        "errors_to_check": [
            "First Workers Day Labor - wrong address (downtown 700 E 7th vs north 4916 N IH 35)",
        ],
    },
    {
        "label": "row219-mobile-health",
        "error_rows": ["219"],
        "suffix": "centraltx",
        "query": "mobile health services for homeless clients",
        "errors_to_check": [
            "Central Health Bridge Mobile - wrong address (601 E 15th vs 5339 I-35 Ste 100)",
            "Central Health Bridge Mobile - fabricated phone 512-978-8130",
            "HOST - fabricated address 1000 E 11th St (mobile team, no fixed office)",
        ],
    },
    {
        "label": "row220-lost-ids",
        "error_rows": ["220"],
        "suffix": "centraltx",
        "query": "My client lost her IDs, which organizations can her get her IDs",
        "errors_to_check": [
            "Austin/Travis County Vital Records - wrong phone (512-972-5017 vs 512-972-5208)",
            "Texas DPS - broken URL path",
        ],
    },
    {
        "label": "trace-8a7e-retail-georgetown",
        "error_rows": ["8a7e6687"],
        "suffix": "centraltx",
        "query": (
            "My client is seeking a part time job in customer services retail\n"
            "Include resources that support the following categories: "
            "Employment & Job Training\n"
            "Focus on resources close to the following location: "
            "Georgetown (Williamson county), TX 78626"
        ),
        "errors_to_check": [
            "Goodwill Wolf Crossing - fabricated Career Center at 916 W University Ave (retail only)",
        ],
    },
    {
        "label": "trace-7c76-retail-georgetown-2",
        "error_rows": ["7c76ced8"],
        "suffix": "centraltx",
        "query": (
            "My client is seeking a part time job in customer services retail\n"
            "Include resources that support the following categories: "
            "Employment & Job Training\n"
            "Focus on resources close to the following location: "
            "Georgetown (Williamson county), TX 78626"
        ),
        "errors_to_check": [
            "Goodwill Wolf Crossing - fabricated Career Center (REPEAT of 8a7e6687)",
            "WSRCA - wrong URLs (/job-seekers vs /seekers, /events vs /calendar/events)",
        ],
    },
    {
        "label": "trace-c62e-volunteer-reading",
        "error_rows": ["c62e8e67"],
        "suffix": "keystone",
        "query": (
            "I am currently working with a 51-year-old Spanish-speaking woman "
            "who lacks natural or family support. She is looking for volunteer "
            "activities to participate in during the day. I believe she is too "
            "young to join Casa de la Amistad, but she is eager to volunteer "
            "if there are any available opportunities.\n"
            "Include the following types of providers: government, community, goodwill\n"
            "Focus on resources close to the following location: reading, pa"
        ),
        "errors_to_check": [
            "Goodwill Keystone Reading - wrong address (606 Court St vs 3001 St. Lawrence Ave)",
            "City of Reading BACs - wrong service type (civic boards, not volunteer opps)",
        ],
    },
    {
        "label": "trace-fc36-dental-insurance",
        "error_rows": ["fc362b17"],
        "suffix": "centraltx",
        "query": "low cost dental insurance",
        "errors_to_check": [
            "All resources - dental CARE not dental INSURANCE (category mismatch)",
            "CommUnityCare - wrong address for dental (5339 N IH 35 is not dental)",
            "People's Community Clinic - doesn't provide dental services",
            "Central Health MAP - PO Box as address instead of physical location",
        ],
    },
    {
        "label": "trace-a03a-rental-assistance",
        "error_rows": ["a03a00b8"],
        "suffix": "centraltx",
        "query": (
            "rental assistance\n"
            "Include resources that support the following categories: "
            "Housing & Shelter, Financial Assistance, Legal Services\n"
            "Include the following types of providers: government, community\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX 78724"
        ),
        "errors_to_check": [
            "Austin Tenants Council - framed as rental assistance but is counseling only",
            "St. Austin Catholic Parish - fabricated date 'Jan 1, 2026' rule",
        ],
    },
]

NUM_RUNS = 2


# ---------------------------------------------------------------------------
# Phoenix span detection (same as experiment script)
# ---------------------------------------------------------------------------


def detect_web_search(trace_spans: list) -> str:
    has_generator = False
    web_search_calls = []
    for span in trace_spans:
        name = span.get("name", "")
        if name == "OpenAIWebSearchGenerator.run":
            has_generator = True
        elif name == "web_search_call":
            web_search_calls.append(span)
    if not has_generator and not web_search_calls:
        return "N/A"
    if not web_search_calls:
        return "NO"
    for span in web_search_calls:
        attrs = span.get("attributes", {})
        action_type = attrs.get("action_type", "") or attrs.get(
            "tool.parameters.action_type", ""
        )
        query = str(attrs.get("query", "") or attrs.get("tool.parameters.query", ""))
        source_urls = attrs.get("source_urls", "") or attrs.get(
            "tool.parameters.source_urls", ""
        )
        if action_type == "search" and source_urls:
            return "YES"
        if query and not query.startswith("calculator"):
            return "YES"
    return "NO"


def fetch_recent_spans(limit_pages: int = 5) -> dict:
    traces: dict[str, list] = defaultdict(list)
    cursor = None
    for _ in range(limit_pages):
        url = f"{PHOENIX_BASE}/v1/projects/{PHOENIX_PROJECT}/spans"
        if cursor:
            url += f"?cursor={cursor}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        spans = data.get("data", [])
        for span in spans:
            tid = span.get("context", {}).get("trace_id", "")
            if tid:
                traces[tid].append(span)
        cursor = data.get("next_cursor")
        if not cursor or not spans:
            break
    return dict(traces)


def find_trace_for_result_id(traces: dict, result_id: str) -> str | None:
    for trace_id, spans in traces.items():
        for span in spans:
            attrs = span.get("attributes", {})
            if result_id in str(attrs.get("input.value", "")):
                return trace_id
    return None


# ---------------------------------------------------------------------------
# API call + SSE parsing
# ---------------------------------------------------------------------------


def call_streaming_api(query: str, suffix: str) -> dict:
    payload = {
        "model": "generate_referrals_rag",
        "messages": [{"role": "user", "content": query}],
        "stream": True,
        "user_email": "retest-qa@test.com",
        "query": query,
        "suffix": suffix,
        "reasoning_effort": "none",
        "prompt_version_id": PROMPT_VERSION_IDS[suffix],
    }
    response = requests.post(
        f"{API_BASE}/chat/completions",
        headers={"Content-Type": "application/json"},
        json=payload,
        stream=True,
        timeout=300,
    )
    response.raise_for_status()

    full_text = ""
    result_id = None
    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data_str = line[len("data: "):]
        if data_str.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(data_str)
            choices = chunk.get("choices", [])
            if choices:
                content = choices[0].get("delta", {}).get("content", "")
                if content:
                    if '{"result_id"' in content:
                        try:
                            result_id = json.loads(content.strip()).get("result_id")
                        except json.JSONDecodeError:
                            m = re.search(r'"result_id"\s*:\s*"([^"]+)"', content)
                            if m:
                                result_id = m.group(1)
                            full_text += content
                    else:
                        full_text += content
        except json.JSONDecodeError:
            continue
    return {"full_text": full_text, "result_id": result_id}


def parse_resources(text: str) -> list[dict]:
    try:
        data = json.loads(text)
        return data.get("resources", [])
    except (json.JSONDecodeError, AttributeError):
        return []


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "label",
    "error_rows",
    "suffix",
    "run",
    "web_search_used",
    "result_id",
    "trace_id",
    "resource_count",
    "resource_names",
    "query_short",
    "full_response",
    "elapsed_seconds",
    "timestamp",
    "error",
]


def _write_csv(path: str, results: list[dict], append: bool = False):
    if not results:
        return
    import os

    mode = "a" if append and os.path.exists(path) else "w"
    with open(path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if mode == "w":
            writer.writeheader()
        writer.writerows(results)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


MAX_WORKERS = 1  # Sequential — server can't handle concurrent streaming requests


def _run_single(prompt: dict, run: int, idx: int, total: int) -> dict:
    """Execute a single API call. Thread-safe — no shared mutable state."""
    label = prompt["label"]
    print(f"  [{idx}/{total}] START {label} | run={run}", flush=True)

    start_time = time.time()
    try:
        api_resp = call_streaming_api(
            query=prompt["query"],
            suffix=prompt["suffix"],
        )
        elapsed = time.time() - start_time
        resources = parse_resources(api_resp["full_text"])
        resource_names = [r.get("name", "?") for r in resources]

        row = {
            "label": label,
            "error_rows": ";".join(prompt["error_rows"]),
            "suffix": prompt["suffix"],
            "run": run,
            "web_search_used": "PENDING",  # filled in batch later
            "result_id": api_resp["result_id"] or "",
            "trace_id": "",
            "resource_count": len(resources),
            "resource_names": "; ".join(resource_names),
            "query_short": prompt["query"][:80],
            "full_response": api_resp["full_text"],
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": datetime.now().isoformat(),
            "error": "",
        }
        print(
            f"  [{idx}/{total}] DONE  {label} run={run}"
            f" -> {len(resources)} resources, {elapsed:.1f}s",
            flush=True,
        )
    except Exception as e:
        elapsed = time.time() - start_time
        row = {
            "label": label,
            "error_rows": ";".join(prompt["error_rows"]),
            "suffix": prompt["suffix"],
            "run": run,
            "web_search_used": "ERROR",
            "result_id": "",
            "trace_id": "",
            "resource_count": 0,
            "resource_names": "",
            "query_short": prompt["query"][:80],
            "full_response": "",
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
        print(f"  [{idx}/{total}] ERROR {label} run={run}: {e}", flush=True)

    return row


def run_retest(skip_first: int = 0, append_to: str | None = None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = append_to or f"app/scripts/retest_qa_results_{ts}.csv"

    # Build work items
    all_items = []
    for prompt in RETEST_PROMPTS:
        for run in range(1, NUM_RUNS + 1):
            all_items.append((prompt, run))
    work_items = all_items[skip_first:]

    total = len(work_items)
    print(f"Retesting QA errors: {total} API calls ({len(RETEST_PROMPTS)} queries x {NUM_RUNS} runs)")
    print(f"Parallel workers: {MAX_WORKERS}")
    print(f"Output: {output_file}")
    print("=" * 70, flush=True)

    # Phase 1: Run all API calls in parallel
    results = [None] * total
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {}
        for idx, (prompt, run) in enumerate(work_items):
            future = executor.submit(_run_single, prompt, run, idx + 1, total)
            future_to_idx[future] = idx

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()

    print(f"\n{'=' * 70}")
    print("All API calls complete. Waiting 8s for Phoenix spans to flush...")
    time.sleep(8)

    # Phase 2: Batch Phoenix span lookup
    print("Fetching Phoenix spans for web search detection...", flush=True)
    try:
        traces = fetch_recent_spans(limit_pages=10)
        print(f"  Fetched {len(traces)} traces with {sum(len(s) for s in traces.values())} spans")

        for row in results:
            if not row or row["web_search_used"] == "ERROR":
                continue
            result_id = row["result_id"]
            if result_id:
                trace_id = find_trace_for_result_id(traces, result_id) or ""
                row["trace_id"] = trace_id
                if trace_id:
                    row["web_search_used"] = detect_web_search(traces[trace_id])
                else:
                    row["web_search_used"] = "TRACE_NOT_FOUND"
            else:
                row["web_search_used"] = "NO_RESULT_ID"
    except Exception as e:
        print(f"  Phoenix error: {e}")
        for row in results:
            if row and row["web_search_used"] == "PENDING":
                row["web_search_used"] = f"PHOENIX_ERROR:{e}"

    # Write final CSV
    _write_csv(output_file, [r for r in results if r], append=bool(append_to))

    print(f"\n{'=' * 70}")
    print(f"Retest complete! {total} results in {output_file}")
    print("\nSummary:")
    ws_counts = defaultdict(int)
    for r in results:
        if r:
            ws_counts[r["web_search_used"]] += 1
    for status, count in sorted(ws_counts.items()):
        print(f"  web_search={status}: {count}")
    print(f"\nAvg resources: {sum(r['resource_count'] for r in results if r) / total:.1f}")
    print(f"Avg time: {sum(r['elapsed_seconds'] for r in results if r) / total:.1f}s")


if __name__ == "__main__":
    import sys

    skip = 0
    append_to = None
    for arg in sys.argv[1:]:
        if arg.startswith("--skip="):
            skip = int(arg.split("=")[1])
        elif arg.startswith("--append="):
            append_to = arg.split("=", 1)[1]
    run_retest(skip_first=skip, append_to=append_to)
