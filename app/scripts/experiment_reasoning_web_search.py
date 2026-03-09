#!/usr/bin/env python3
"""
Experiment: Does reasoning_effort affect web search usage in gpt-5.1?

Compares reasoning_effort="none" vs "low" across prompts that historically
skip web search. Calls the streaming /chat/completions endpoint (same as frontend)
and parses SSE to collect full responses, then queries local Phoenix for web search spans.

Usage:
    python app/scripts/experiment_reasoning_web_search.py
"""

from __future__ import annotations

import csv
import json
import re
import time
from collections import defaultdict
from datetime import datetime

import requests

API_BASE = "http://localhost:3000"
PHOENIX_BASE = "http://localhost:6006"
PHOENIX_PROJECT = "local-docker-project"

# Local Phoenix prompt version IDs matching production
# (copied from deployed Phoenix via `make copy-prompts`)
PROMPT_VERSION_IDS = {
    "centraltx": "UHJvbXB0VmVyc2lvbjoxMg==",  # "Clarifying county eligibility" (4853 chars)
    "keystone": "UHJvbXB0VmVyc2lvbjoxMw==",  # "JSON instructions" (4354 chars)
}

# Prompts that previously SKIPPED web search (~48% skip rate on centraltx)
TEST_PROMPTS = [
    {
        "query": "Housing resources Austin 78745",
        "suffix": "centraltx",
        "label": "housing-austin",
        "expected_web_search": False,
    },
    {
        "query": "Employment & Job Training Austin 78701",
        "suffix": "centraltx",
        "label": "employment-austin",
        "expected_web_search": False,
    },
    {
        "query": "Lost IDs Austin TX",
        "suffix": "centraltx",
        "label": "lost-ids-austin",
        "expected_web_search": False,
    },
    {
        "query": "Household items for formerly homeless client Austin",
        "suffix": "centraltx",
        "label": "household-items-austin",
        "expected_web_search": False,
    },
    {
        "query": "Cap metro cold weather information",
        "suffix": "centraltx",
        "label": "cap-metro-cold",
        "expected_web_search": False,
    },
    {
        "query": "Paraplegic support coordination Reading PA",
        "suffix": "keystone",
        "label": "paraplegic-reading",
        "expected_web_search": False,
    },
    # Control prompts that DID use web search previously
    {
        "query": "Emergency rent assistance for single mother in Austin 78741",
        "suffix": "centraltx",
        "label": "control-rent-assist",
        "expected_web_search": True,
    },
    {
        "query": "Free dental care for uninsured adults in Reading PA",
        "suffix": "keystone",
        "label": "control-dental-reading",
        "expected_web_search": True,
    },
]

CONDITIONS = ["none", "low"]
NUM_RUNS = 2


# ---------------------------------------------------------------------------
# Phoenix span detection (adapted from phoenix-sheets-sync/sync_to_sheets.py)
# ---------------------------------------------------------------------------


def detect_web_search(trace_spans: list) -> str:
    """Detect whether web search was used in a trace.

    Returns: YES, NO, DISTANCE_ONLY, or N/A.
    """
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

    has_real_search = False
    has_distance = False

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
            has_real_search = True
        elif query.startswith("calculator:"):
            calc_rest = query.split(":", 1)[1].strip()
            if "distance" in calc_rest:
                has_distance = True
        else:
            if query and not query.startswith("calculator"):
                has_real_search = True

    if has_real_search:
        return "YES"
    if has_distance:
        return "DISTANCE_ONLY"
    return "NO"


def count_web_search_calls(trace_spans: list) -> int:
    """Count real (non-calculator) web search calls in a trace."""
    count = 0
    for span in trace_spans:
        if span.get("name") != "web_search_call":
            continue
        attrs = span.get("attributes", {})
        query = str(attrs.get("query", "") or attrs.get("tool.parameters.query", ""))
        if query and not query.startswith("calculator:"):
            count += 1
    return count


def fetch_trace_spans(trace_id: str) -> list:
    """Fetch all spans for a given trace_id from local Phoenix."""
    all_spans = []
    cursor = None

    for _ in range(10):  # max pages
        url = f"{PHOENIX_BASE}/v1/projects/{PHOENIX_PROJECT}/spans"
        if cursor:
            url += f"?cursor={cursor}"

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        spans = data.get("data", [])

        for span in spans:
            ctx = span.get("context", {})
            if ctx.get("trace_id") == trace_id:
                all_spans.append(span)

        cursor = data.get("next_cursor")
        if not cursor or not spans:
            break

    return all_spans


def fetch_recent_spans(limit_pages: int = 5) -> dict:
    """Fetch recent spans and group by trace_id.

    Returns {trace_id: [span, ...]}.
    """
    traces = defaultdict(list)
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
            ctx = span.get("context", {})
            tid = ctx.get("trace_id", "")
            if tid:
                traces[tid].append(span)

        cursor = data.get("next_cursor")
        if not cursor or not spans:
            break

    return dict(traces)


def find_trace_for_result_id(traces: dict, result_id: str) -> str | None:
    """Find the trace_id that contains a span referencing the given result_id."""
    for trace_id, spans in traces.items():
        for span in spans:
            attrs = span.get("attributes", {})
            # result_id appears in input.value or output.value of SaveResult span
            input_val = str(attrs.get("input.value", ""))
            if result_id in input_val:
                return trace_id
    return None


# ---------------------------------------------------------------------------
# API call + SSE parsing
# ---------------------------------------------------------------------------


def call_streaming_api(query: str, suffix: str, reasoning_effort: str) -> dict:
    """Call the streaming /chat/completions endpoint and parse SSE response."""
    payload = {
        "model": "generate_referrals_rag",
        "messages": [{"role": "user", "content": query}],
        "stream": True,
        "user_email": "experiment@test.com",
        "query": query,
        "suffix": suffix,
        "reasoning_effort": reasoning_effort,
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
        data_str = line[len("data: ") :]
        if data_str.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(data_str)
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    if '{"result_id"' in content:
                        try:
                            rid_data = json.loads(content.strip())
                            result_id = rid_data.get("result_id")
                        except json.JSONDecodeError:
                            match = re.search(r'"result_id"\s*:\s*"([^"]+)"', content)
                            if match:
                                result_id = match.group(1)
                            full_text += content
                    else:
                        full_text += content
        except json.JSONDecodeError:
            continue

    return {"full_text": full_text, "result_id": result_id}


def parse_resources(text: str) -> list[str]:
    """Extract resource names from the JSON response text."""
    try:
        data = json.loads(text)
        return [r.get("name", "Unknown") for r in data.get("resources", [])]
    except (json.JSONDecodeError, AttributeError):
        return []


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "query",
    "label",
    "suffix",
    "reasoning_effort",
    "run",
    "expected_web_search",
    "web_search_used",
    "web_search_count",
    "result_id",
    "trace_id",
    "resource_count",
    "resource_names",
    "response_length",
    "elapsed_seconds",
    "timestamp",
    "error",
]


def _write_csv(path: str, results: list[dict]):
    """Write results to CSV."""
    if not results:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------


def run_experiment():
    """Run the full experiment."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"app/scripts/experiment_results_{ts}.csv"

    results = []
    total = len(TEST_PROMPTS) * len(CONDITIONS) * NUM_RUNS
    current = 0

    print(f"Running experiment: {total} total API calls")
    print(f"Prompts: {len(TEST_PROMPTS)}, Conditions: {CONDITIONS}, Runs: {NUM_RUNS}")
    print(f"Output: {output_file}")
    print("=" * 70)

    for prompt in TEST_PROMPTS:
        for condition in CONDITIONS:
            for run in range(1, NUM_RUNS + 1):
                current += 1
                label = prompt["label"]
                print(
                    f"\n[{current}/{total}] {label} | "
                    f"reasoning={condition} | run={run}"
                )

                start_time = time.time()
                try:
                    api_resp = call_streaming_api(
                        query=prompt["query"],
                        suffix=prompt["suffix"],
                        reasoning_effort=condition,
                    )
                    elapsed = time.time() - start_time

                    resources = parse_resources(api_resp["full_text"])
                    result_id = api_resp["result_id"]

                    # Wait for Phoenix spans to flush before querying
                    print("  Waiting 5s for Phoenix spans to flush...")
                    time.sleep(5)

                    # Query Phoenix to detect web search
                    web_search_used = "UNKNOWN"
                    web_search_count = 0
                    trace_id = ""

                    if result_id:
                        try:
                            trace_spans_by_id = fetch_recent_spans(limit_pages=3)
                            trace_id = find_trace_for_result_id(
                                trace_spans_by_id, result_id
                            )
                            if trace_id:
                                spans = trace_spans_by_id[trace_id]
                                web_search_used = detect_web_search(spans)
                                web_search_count = count_web_search_calls(spans)
                            else:
                                web_search_used = "TRACE_NOT_FOUND"
                        except Exception as e:
                            web_search_used = f"PHOENIX_ERROR:{e}"

                    row = {
                        "query": prompt["query"],
                        "label": label,
                        "suffix": prompt["suffix"],
                        "reasoning_effort": condition,
                        "run": run,
                        "expected_web_search": prompt["expected_web_search"],
                        "web_search_used": web_search_used,
                        "web_search_count": web_search_count,
                        "result_id": result_id or "",
                        "trace_id": trace_id or "",
                        "resource_count": len(resources),
                        "resource_names": "; ".join(resources),
                        "response_length": len(api_resp["full_text"]),
                        "elapsed_seconds": round(elapsed, 1),
                        "timestamp": datetime.now().isoformat(),
                        "error": "",
                    }

                    print(
                        f"  -> {len(resources)} resources, "
                        f"web_search={web_search_used} ({web_search_count} calls), "
                        f"{elapsed:.1f}s"
                    )

                except Exception as e:
                    elapsed = time.time() - start_time
                    row = {
                        "query": prompt["query"],
                        "label": label,
                        "suffix": prompt["suffix"],
                        "reasoning_effort": condition,
                        "run": run,
                        "expected_web_search": prompt["expected_web_search"],
                        "web_search_used": "ERROR",
                        "web_search_count": 0,
                        "result_id": "",
                        "trace_id": "",
                        "resource_count": 0,
                        "resource_names": "",
                        "response_length": 0,
                        "elapsed_seconds": round(elapsed, 1),
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                    }
                    print(f"  -> ERROR: {e}")

                results.append(row)
                _write_csv(output_file, results)

    print("\n" + "=" * 70)
    print(f"Experiment complete! {len(results)} results written to {output_file}")
    print_summary(results)


def print_summary(results: list[dict]):
    """Print a summary table comparing conditions."""
    print("\n=== SUMMARY ===\n")

    for condition in CONDITIONS:
        cond_results = [r for r in results if r["reasoning_effort"] == condition]
        n = len(cond_results)
        if not n:
            continue
        avg_resources = sum(r["resource_count"] for r in cond_results) / n
        avg_time = sum(r["elapsed_seconds"] for r in cond_results) / n
        ws_yes = sum(1 for r in cond_results if r["web_search_used"] == "YES")
        ws_no = sum(1 for r in cond_results if r["web_search_used"] == "NO")
        ws_dist = sum(1 for r in cond_results if r["web_search_used"] == "DISTANCE_ONLY")
        errors = sum(1 for r in cond_results if r["error"])

        print(f"reasoning_effort={condition}:")
        print(f"  Runs: {n}")
        print(f"  Web search YES: {ws_yes}/{n} ({ws_yes/n:.0%})")
        print(f"  Web search NO:  {ws_no}/{n} ({ws_no/n:.0%})")
        if ws_dist:
            print(f"  Web search DISTANCE_ONLY: {ws_dist}/{n}")
        print(f"  Avg resources: {avg_resources:.1f}")
        print(f"  Avg time: {avg_time:.1f}s")
        if errors:
            print(f"  Errors: {errors}")
        print()

    # Per-prompt comparison
    print(f"{'Label':<25} {'none':>20} {'low':>20}")
    print("-" * 65)

    labels = list(dict.fromkeys(r["label"] for r in results))
    for label in labels:
        parts = []
        for condition in CONDITIONS:
            rows = [
                r
                for r in results
                if r["label"] == label and r["reasoning_effort"] == condition
            ]
            if rows:
                ws = sum(1 for r in rows if r["web_search_used"] == "YES")
                avg_res = sum(r["resource_count"] for r in rows) / len(rows)
                parts.append(f"{avg_res:.0f}res ws={ws}/{len(rows)}")
            else:
                parts.append("N/A")
        print(f"{label:<25} {parts[0]:>20} {parts[1]:>20}")


if __name__ == "__main__":
    run_experiment()
