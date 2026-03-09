#!/usr/bin/env python3
"""
Targeted retest: prompt specifically for resources that weren't returned
in the broad retest, to check if their original QA errors persist.

Usage:
    python app/scripts/retest_targeted.py
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

PROMPT_VERSION_IDS = {
    "centraltx": "UHJvbXB0VmVyc2lvbjoxMg==",
    "keystone": "UHJvbXB0VmVyc2lvbjoxMw==",
}

TARGETED_PROMPTS = [
    {
        "label": "targeted-goodwill-keystone-shower",
        "suffix": "keystone",
        "query": (
            "My client needs access to showers and restrooms. "
            "Are there any Goodwill locations or shelters with shower "
            "facilities in Reading PA?\n"
            "Focus on resources close to the following location: Reading, PA"
        ),
        "target_resource": "Goodwill Keystone Area",
        "error_check": "wrong phone 717-232-1831 or wrong address 3001 St. Lawrence Ave",
        "bad_patterns": ["717-232-1831"],
    },
    {
        "label": "targeted-united-way-berks",
        "suffix": "keystone",
        "query": (
            "What resources does United Way of Berks County offer for "
            "basic needs assistance?\n"
            "Focus on resources close to the following location: Reading, PA"
        ),
        "target_resource": "United Way of Berks County",
        "error_check": "wrong address 631 Penn St (correct: 25 N 2nd St Suite 101)",
        "bad_patterns": ["631 Penn St", "631 Penn Street"],
    },
    {
        "label": "targeted-bcap-berks",
        "suffix": "keystone",
        "query": (
            "My client needs help with utility bills and housing. "
            "What does the Berks Community Action Program (BCAP) offer?\n"
            "Focus on resources close to the following location: Reading, PA"
        ),
        "target_resource": "BCAP",
        "error_check": "wrong URL berkscap.org (correct: bcapberks.org)",
        "bad_patterns": ["berkscap.org"],
    },
    {
        "label": "targeted-bucks-county-hub",
        "suffix": "keystone",
        "query": (
            "My client needs daytime shelter and human services support "
            "in Bucks County PA. What resources are available?\n"
            "Focus on resources close to the following location: Doylestown, PA"
        ),
        "target_resource": "Bucks County Human Services",
        "error_check": "wrong phone 215-348-6000 (courthouse number)",
        "bad_patterns": ["215-348-6000"],
    },
    {
        "label": "targeted-starkey-hearing",
        "suffix": "centraltx",
        "query": (
            "My client needs hearing aid assistance and can't afford to "
            "buy them. What programs help with free or low-cost hearing aids "
            "in Austin TX?"
        ),
        "target_resource": "Starkey Hearing Foundation",
        "error_check": "wrong address 6801 vs 6700 Washington Ave S",
        "bad_patterns": ["6801"],
    },
    {
        "label": "targeted-wilco-care",
        "suffix": "centraltx",
        "query": (
            "My client lives in Williamson County TX and needs help with "
            "hearing aids. Does WilCo Care or any Williamson County program "
            "cover hearing aids?\n"
            "Focus on resources close to the following location: "
            "Round Rock (Williamson county), TX"
        ),
        "target_resource": "WilCo Care",
        "error_check": "WilCo Care doesn't cover hearing aids (only medical/dental/vision)",
        "bad_patterns": [],
    },
    {
        "label": "targeted-day-labor-austin",
        "suffix": "centraltx",
        "query": (
            "My client needs immediate day labor work opportunities in "
            "Austin TX. What is the City of Austin's day labor program?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX 78704"
        ),
        "target_resource": "City of Austin Day Labor / First Workers",
        "error_check": "wrong address 2514 Sol Wilson / wrong phone 512-974-1730",
        "bad_patterns": ["2514 Sol Wilson", "512-974-1730"],
    },
    {
        "label": "targeted-svdp-austin",
        "suffix": "centraltx",
        "query": (
            "My client is a homeless veteran and needs emergency financial "
            "assistance. What does St. Vincent de Paul offer in Austin TX?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "St. Vincent de Paul Austin",
        "error_check": "broken URL austinsvdp.info/locate-assistance (404)",
        "bad_patterns": ["austinsvdp.info/locate-assistance"],
    },
    {
        "label": "targeted-central-health-bridge",
        "suffix": "centraltx",
        "query": (
            "Does Central Health have a mobile clinic or Bridge program "
            "for homeless clients in Austin TX?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "Central Health Bridge Mobile",
        "error_check": "wrong address 601 E 15th / fabricated phone 512-978-8130",
        "bad_patterns": ["601 E 15th", "512-978-8130"],
    },
    {
        "label": "targeted-host-outreach",
        "suffix": "centraltx",
        "query": (
            "My client needs help from Austin's HOST (Homeless Outreach "
            "Street Team). How do I connect them?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "HOST",
        "error_check": "fabricated address 1000 E 11th St (mobile team, no fixed office)",
        "bad_patterns": ["1000 E 11th"],
    },
    {
        "label": "targeted-vital-records",
        "suffix": "centraltx",
        "query": (
            "My client needs a copy of their birth certificate from "
            "Austin/Travis County Vital Records. What is the phone number "
            "and address?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "Austin/Travis County Vital Records",
        "error_check": "wrong phone 512-972-5017 (correct: 512-972-5208)",
        "bad_patterns": ["512-972-5017"],
    },
    {
        "label": "targeted-wsrca",
        "suffix": "centraltx",
        "query": (
            "My client needs job search help through Workforce Solutions "
            "Rural Capital Area (WSRCA) near Georgetown TX.\n"
            "Focus on resources close to the following location: "
            "Georgetown (Williamson county), TX 78626"
        ),
        "target_resource": "WSRCA",
        "error_check": "wrong URLs: /job-seekers (should be /seekers), /events (should be /calendar/events)",
        "bad_patterns": ["/job-seekers", "/events"],
    },
    {
        "label": "targeted-st-austin-parish",
        "suffix": "centraltx",
        "query": (
            "Does St. Austin Catholic Parish offer any rental or financial "
            "assistance in Austin TX?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX 78724"
        ),
        "target_resource": "St. Austin Catholic Parish",
        "error_check": "fabricated date 'Jan 1, 2026' rule",
        "bad_patterns": ["Jan 1", "January 1"],
    },
    {
        "label": "targeted-cpr-cert",
        "suffix": "centraltx",
        "query": (
            "My client needs CPR certification in Austin TX. Where can "
            "they get trained?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "CPR Certification Austin",
        "error_check": "wrong address 3430 W William Cannon (correct: 701 Tillery St)",
        "bad_patterns": ["3430 W William Cannon", "3430 William Cannon"],
    },
    {
        "label": "targeted-mission-possible",
        "suffix": "centraltx",
        "query": (
            "My client needs groceries. Is Mission Possible B.A.G.S. "
            "food pantry currently accepting new clients in Austin TX?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "Mission Possible B.A.G.S.",
        "error_check": "should mention 'at capacity' status",
        "bad_patterns": [],
    },
    {
        "label": "targeted-ssa-child-ssn",
        "suffix": "centraltx",
        "query": (
            "My client's child lost their Social Security card. Can they "
            "replace it online using the SSA website, or do they need to "
            "visit an office?\n"
            "Focus on resources close to the following location: "
            "Austin (Travis county), TX"
        ),
        "target_resource": "SSA",
        "error_check": "online tool doesn't work for children SSN replacement",
        "bad_patterns": [],
    },
]


# ---------------------------------------------------------------------------
# Reuse helpers from retest_qa_errors.py
# ---------------------------------------------------------------------------


def call_streaming_api(query: str, suffix: str) -> dict:
    payload = {
        "model": "generate_referrals_rag",
        "messages": [{"role": "user", "content": query}],
        "stream": True,
        "user_email": "retest-targeted@test.com",
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
        source_urls = attrs.get("source_urls", "") or attrs.get(
            "tool.parameters.source_urls", ""
        )
        query = str(attrs.get("query", "") or attrs.get("tool.parameters.query", ""))
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
# Main
# ---------------------------------------------------------------------------


def run_targeted():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"app/scripts/retest_targeted_{ts}.csv"

    total = len(TARGETED_PROMPTS)
    print(f"Targeted retest: {total} API calls (1 run each)")
    print(f"Output: {output_file}")
    print("=" * 70, flush=True)

    results = []

    for i, prompt in enumerate(TARGETED_PROMPTS, 1):
        label = prompt["label"]
        print(f"\n[{i}/{total}] {label}", flush=True)

        start = time.time()
        try:
            api_resp = call_streaming_api(prompt["query"], prompt["suffix"])
            elapsed = time.time() - start

            try:
                data = json.loads(api_resp["full_text"])
                resources = data.get("resources", [])
            except (json.JSONDecodeError, AttributeError):
                resources = []

            resource_names = [r.get("name", "?") for r in resources]
            print(f"  -> {len(resources)} resources, {elapsed:.1f}s", flush=True)

            # Check for target resource and errors
            target = prompt["target_resource"].lower()
            matched = [
                r for r in resources
                if target in r.get("name", "").lower()
                or target in json.dumps(r).lower()
            ]

            error_found = "N/A"
            error_details = ""
            if matched:
                res_json = json.dumps(matched[0])
                bad = prompt["bad_patterns"]
                hits = [p for p in bad if p in res_json]
                if hits:
                    error_found = "YES"
                    error_details = f"Bad patterns found: {hits}"
                    print(f"  ** ERROR PERSISTS: {hits}", flush=True)
                elif bad:
                    error_found = "NO"
                    error_details = "Target resource present, bad patterns absent"
                    print(f"  OK: target present, no bad patterns", flush=True)
                else:
                    error_found = "MANUAL"
                    error_details = "No automated check — needs manual review"
                    print(f"  MANUAL: needs human review", flush=True)

                # Print the matched resource details
                m = matched[0]
                print(f"  Resource: {m.get('name', '?')}", flush=True)
                print(f"    phones: {m.get('phones', [])}", flush=True)
                print(f"    addresses: {m.get('addresses', [])}", flush=True)
                print(f"    website: {m.get('website', '')}", flush=True)
                desc = m.get("description", "")[:150]
                print(f"    description: {desc}...", flush=True)
            else:
                error_found = "NOT_RETURNED"
                error_details = "Target resource not in response"
                print(f"  Target resource NOT returned", flush=True)
                # Show what was returned
                for n in resource_names[:5]:
                    print(f"    - {n}", flush=True)

            row = {
                "label": label,
                "suffix": prompt["suffix"],
                "target_resource": prompt["target_resource"],
                "error_check": prompt["error_check"],
                "error_found": error_found,
                "error_details": error_details,
                "resource_count": len(resources),
                "resource_names": "; ".join(resource_names),
                "result_id": api_resp["result_id"] or "",
                "elapsed_seconds": round(elapsed, 1),
                "full_response": api_resp["full_text"],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            elapsed = time.time() - start
            row = {
                "label": label,
                "suffix": prompt["suffix"],
                "target_resource": prompt["target_resource"],
                "error_check": prompt["error_check"],
                "error_found": "ERROR",
                "error_details": str(e),
                "resource_count": 0,
                "resource_names": "",
                "result_id": "",
                "elapsed_seconds": round(elapsed, 1),
                "full_response": "",
                "timestamp": datetime.now().isoformat(),
            }
            print(f"  ERROR: {e}", flush=True)

        results.append(row)

    # Write CSV
    fields = [
        "label", "suffix", "target_resource", "error_check",
        "error_found", "error_details", "resource_count", "resource_names",
        "result_id", "elapsed_seconds", "full_response", "timestamp",
    ]
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"Done! {total} results in {output_file}\n")

    counts = defaultdict(int)
    for r in results:
        counts[r["error_found"]] += 1

    print("Results:")
    for status in ["YES", "NO", "NOT_RETURNED", "MANUAL", "N/A", "ERROR"]:
        if counts[status]:
            print(f"  {status}: {counts[status]}")

    print("\nDetailed:")
    for r in results:
        icon = {
            "YES": "X", "NO": "OK", "NOT_RETURNED": "?",
            "MANUAL": "!", "ERROR": "ERR",
        }.get(r["error_found"], "?")
        print(f"  [{icon}] {r['target_resource']}: {r['error_found']} — {r['error_details'][:80]}")


if __name__ == "__main__":
    run_targeted()
