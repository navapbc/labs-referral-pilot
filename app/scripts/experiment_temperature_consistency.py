#!/usr/bin/env python3
"""
Experiment: Does temperature affect resource consistency with reasoning_effort="none"?

Tests gpt-5.1 with no reasoning at different temperature settings (0.0, 0.3, 0.6, 0.9)
to measure how consistently the same resources are returned across repeated runs.

Each prompt is run N times per temperature. We then measure:
- Overlap of resource names across runs (Jaccard similarity)
- Exact match rate (how often the exact same set of resources appears)
- Average resource count

Usage:
    python app/scripts/experiment_temperature_consistency.py
"""

from __future__ import annotations

import csv
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime

import requests

API_BASE = "http://localhost:3000"
PHOENIX_BASE = "http://localhost:6006"
PHOENIX_PROJECT = "local-docker-project"

PROMPT_VERSION_IDS = {
    "centraltx": "UHJvbXB0VmVyc2lvbjoxMg==",
    "keystone": "UHJvbXB0VmVyc2lvbjoxMw==",
}

# Test prompts - representative queries
TEST_PROMPTS = [
    {
        "query": "Housing resources Austin 78745",
        "suffix": "centraltx",
        "label": "housing-austin",
    },
    {
        "query": "Employment & Job Training Austin 78701",
        "suffix": "centraltx",
        "label": "employment-austin",
    },
    {
        "query": "Emergency rent assistance for single mother in Austin 78741",
        "suffix": "centraltx",
        "label": "rent-assist-austin",
    },
    {
        "query": "Free dental care for uninsured adults in Reading PA",
        "suffix": "keystone",
        "label": "dental-reading",
    },
]

TEMPERATURES = [0.0, 0.3, 0.6, 0.9]
NUM_RUNS = 3  # Runs per prompt per temperature


# ---------------------------------------------------------------------------
# API call + SSE parsing (reused from experiment_reasoning_web_search.py)
# ---------------------------------------------------------------------------


def call_streaming_api(
    query: str, suffix: str, reasoning_effort: str, temperature: float
) -> dict:
    """Call the streaming /chat/completions endpoint and parse SSE response."""
    payload = {
        "model": "generate_referrals_rag",
        "messages": [{"role": "user", "content": query}],
        "stream": True,
        "user_email": "experiment-temp@test.com",
        "query": query,
        "suffix": suffix,
        "reasoning_effort": reasoning_effort,
        "temperature": temperature,
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
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    if '{"result_id"' in content:
                        try:
                            rid_data = json.loads(content.strip())
                            result_id = rid_data.get("result_id")
                        except json.JSONDecodeError:
                            match = re.search(
                                r'"result_id"\s*:\s*"([^"]+)"', content
                            )
                            if match:
                                result_id = match.group(1)
                            full_text += content
                    else:
                        full_text += content
        except json.JSONDecodeError:
            continue

    return {"full_text": full_text, "result_id": result_id}


def parse_resources(text: str) -> list[dict]:
    """Extract resource objects from the JSON response text."""
    try:
        data = json.loads(text)
        return data.get("resources", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def resource_names(resources: list[dict]) -> list[str]:
    """Extract sorted resource names."""
    return sorted(r.get("name", "Unknown") for r in resources)


# ---------------------------------------------------------------------------
# Consistency metrics
# ---------------------------------------------------------------------------


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def compute_consistency_metrics(runs: list[list[str]]) -> dict:
    """Compute consistency metrics across multiple runs.

    Args:
        runs: List of lists of resource names (one per run)

    Returns:
        Dict with avg_jaccard, exact_match_rate, avg_count, unique_resources_seen
    """
    if not runs:
        return {
            "avg_jaccard": 0,
            "min_jaccard": 0,
            "exact_match_rate": 0,
            "avg_count": 0,
            "unique_resources_seen": 0,
        }

    # Convert each run to a frozenset for comparison
    sets = [frozenset(r) for r in runs]

    # Pairwise Jaccard similarity
    jaccards = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            jaccards.append(jaccard_similarity(sets[i], sets[j]))

    # Exact match: how many runs returned the exact same set?
    counter = Counter(sets)
    most_common_count = counter.most_common(1)[0][1] if counter else 0
    exact_match_rate = most_common_count / len(runs)

    # All unique resources seen across runs
    all_resources = set()
    for r in runs:
        all_resources.update(r)

    return {
        "avg_jaccard": sum(jaccards) / len(jaccards) if jaccards else 1.0,
        "min_jaccard": min(jaccards) if jaccards else 1.0,
        "exact_match_rate": exact_match_rate,
        "avg_count": sum(len(r) for r in runs) / len(runs),
        "unique_resources_seen": len(all_resources),
    }


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

RAW_CSV_FIELDS = [
    "query",
    "label",
    "suffix",
    "temperature",
    "reasoning_effort",
    "run",
    "resource_count",
    "resource_names",
    "response_length",
    "elapsed_seconds",
    "timestamp",
    "error",
]

SUMMARY_CSV_FIELDS = [
    "label",
    "suffix",
    "temperature",
    "reasoning_effort",
    "num_runs",
    "avg_resource_count",
    "unique_resources_seen",
    "avg_jaccard",
    "min_jaccard",
    "exact_match_rate",
    "all_resource_names",
]


def write_csv(path: str, rows: list[dict], fields: list[str]):
    """Write results to CSV."""
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------


def run_experiment():
    """Run the temperature consistency experiment."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_file = f"app/scripts/temp_experiment_raw_{ts}.csv"
    summary_file = f"app/scripts/temp_experiment_summary_{ts}.csv"
    reasoning = "none"

    raw_results = []
    # {(label, temperature): [list_of_resource_names_per_run]}
    runs_by_key: dict[tuple, list[list[str]]] = defaultdict(list)

    total = len(TEST_PROMPTS) * len(TEMPERATURES) * NUM_RUNS
    current = 0

    print(f"Temperature Consistency Experiment")
    print(f"Model: gpt-5.1, reasoning_effort={reasoning}")
    print(f"Temperatures: {TEMPERATURES}")
    print(f"Prompts: {len(TEST_PROMPTS)}, Runs per combo: {NUM_RUNS}")
    print(f"Total API calls: {total}")
    print(f"Raw output: {raw_file}")
    print(f"Summary output: {summary_file}")
    print("=" * 70)

    for prompt in TEST_PROMPTS:
        for temp in TEMPERATURES:
            for run in range(1, NUM_RUNS + 1):
                current += 1
                label = prompt["label"]
                print(
                    f"\n[{current}/{total}] {label} | "
                    f"temp={temp} | run={run}"
                )

                start_time = time.time()
                try:
                    api_resp = call_streaming_api(
                        query=prompt["query"],
                        suffix=prompt["suffix"],
                        reasoning_effort=reasoning,
                        temperature=temp,
                    )
                    elapsed = time.time() - start_time

                    resources = parse_resources(api_resp["full_text"])
                    names = resource_names(resources)
                    runs_by_key[(label, temp)].append(names)

                    row = {
                        "query": prompt["query"],
                        "label": label,
                        "suffix": prompt["suffix"],
                        "temperature": temp,
                        "reasoning_effort": reasoning,
                        "run": run,
                        "resource_count": len(resources),
                        "resource_names": "; ".join(names),
                        "response_length": len(api_resp["full_text"]),
                        "elapsed_seconds": round(elapsed, 1),
                        "timestamp": datetime.now().isoformat(),
                        "error": "",
                    }

                    print(
                        f"  -> {len(resources)} resources, "
                        f"{elapsed:.1f}s: {', '.join(names[:3])}..."
                    )

                except Exception as e:
                    elapsed = time.time() - start_time
                    row = {
                        "query": prompt["query"],
                        "label": label,
                        "suffix": prompt["suffix"],
                        "temperature": temp,
                        "reasoning_effort": reasoning,
                        "run": run,
                        "resource_count": 0,
                        "resource_names": "",
                        "response_length": 0,
                        "elapsed_seconds": round(elapsed, 1),
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                    }
                    print(f"  -> ERROR: {e}")

                raw_results.append(row)
                write_csv(raw_file, raw_results, RAW_CSV_FIELDS)

    # Build summary
    summary_rows = []
    for prompt in TEST_PROMPTS:
        for temp in TEMPERATURES:
            key = (prompt["label"], temp)
            runs = runs_by_key.get(key, [])
            if not runs:
                continue
            metrics = compute_consistency_metrics(runs)

            all_names = set()
            for r in runs:
                all_names.update(r)

            summary_rows.append(
                {
                    "label": prompt["label"],
                    "suffix": prompt["suffix"],
                    "temperature": temp,
                    "reasoning_effort": reasoning,
                    "num_runs": len(runs),
                    "avg_resource_count": round(metrics["avg_count"], 1),
                    "unique_resources_seen": metrics["unique_resources_seen"],
                    "avg_jaccard": round(metrics["avg_jaccard"], 3),
                    "min_jaccard": round(metrics["min_jaccard"], 3),
                    "exact_match_rate": round(metrics["exact_match_rate"], 2),
                    "all_resource_names": "; ".join(sorted(all_names)),
                }
            )

    write_csv(summary_file, summary_rows, SUMMARY_CSV_FIELDS)

    print("\n" + "=" * 70)
    print(f"Experiment complete! {len(raw_results)} results.")
    print(f"Raw: {raw_file}")
    print(f"Summary: {summary_file}")
    print_summary(summary_rows)


def print_summary(summary_rows: list[dict]):
    """Print a formatted summary table."""
    print("\n=== CONSISTENCY SUMMARY ===\n")
    print(
        f"{'Label':<25} {'Temp':>5} {'AvgRes':>7} {'Unique':>7} "
        f"{'Jaccard':>8} {'MinJac':>7} {'Exact%':>7}"
    )
    print("-" * 70)

    current_label = ""
    for row in summary_rows:
        label = row["label"]
        if label != current_label:
            if current_label:
                print()  # Blank line between prompts
            current_label = label

        print(
            f"{label:<25} {row['temperature']:>5.1f} "
            f"{row['avg_resource_count']:>7.1f} "
            f"{row['unique_resources_seen']:>7} "
            f"{row['avg_jaccard']:>8.3f} "
            f"{row['min_jaccard']:>7.3f} "
            f"{row['exact_match_rate']:>6.0%}"
        )

    # Cross-temperature comparison
    print("\n=== TEMPERATURE COMPARISON (averaged across prompts) ===\n")
    for temp in TEMPERATURES:
        temp_rows = [r for r in summary_rows if r["temperature"] == temp]
        if not temp_rows:
            continue
        avg_jac = sum(r["avg_jaccard"] for r in temp_rows) / len(temp_rows)
        avg_min = sum(r["min_jaccard"] for r in temp_rows) / len(temp_rows)
        avg_exact = sum(r["exact_match_rate"] for r in temp_rows) / len(temp_rows)
        avg_unique = sum(r["unique_resources_seen"] for r in temp_rows) / len(
            temp_rows
        )
        print(
            f"  temp={temp:.1f}: "
            f"avg_jaccard={avg_jac:.3f}, "
            f"min_jaccard={avg_min:.3f}, "
            f"exact_match={avg_exact:.0%}, "
            f"avg_unique_resources={avg_unique:.1f}"
        )


if __name__ == "__main__":
    run_experiment()
