#!/usr/bin/env python3
"""
Compare resource descriptions and contact info across repeated runs - PA/Keystone region.

Runs each prompt 3x at temp=0.3 and temp=0.9, saves full JSON, then compares
descriptions/phones/addresses/websites for resources that appear across runs.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import requests

API_BASE = "http://localhost:3000"

PROMPT_VERSION_IDS = {
    "keystone": "UHJvbXB0VmVyc2lvbjoxMw==",
}

TEST_PROMPTS = [
    {
        "query": "Emergency housing assistance for a family with children facing eviction in Reading PA",
        "suffix": "keystone",
        "label": "housing-family-reading",
    },
    {
        "query": "Food pantries and meal programs for seniors in Berks County PA",
        "suffix": "keystone",
        "label": "food-seniors-berks",
    },
    {
        "query": "Mental health counseling for uninsured adult in Lancaster PA",
        "suffix": "keystone",
        "label": "mental-health-lancaster",
    },
]

TEMPERATURES = [0.3, 0.9]
NUM_RUNS = 3


def call_api(query: str, suffix: str, temperature: float) -> dict:
    payload = {
        "model": "generate_referrals_rag",
        "messages": [{"role": "user", "content": query}],
        "stream": True,
        "user_email": "experiment-details-pa@test.com",
        "query": query,
        "suffix": suffix,
        "reasoning_effort": "none",
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
                if content and '{"result_id"' not in content:
                    full_text += content
        except json.JSONDecodeError:
            continue

    try:
        return json.loads(full_text)
    except json.JSONDecodeError:
        return {"resources": [], "raw": full_text[:500]}


def normalize_name(name: str) -> str:
    normalized = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    normalized = re.sub(r"\s*[–-]\s*$", "", normalized).strip()
    normalized = normalized.replace("–", "-").replace("—", "-")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def group_resources_across_runs(
    all_runs: list[list[dict]],
) -> dict[str, list[dict]]:
    canonical_map: dict[str, str] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)

    for run_idx, resources in enumerate(all_runs):
        for res in resources:
            name = res.get("name", "")
            norm = normalize_name(name)

            best_match = None
            best_score = 0.0
            for existing, canonical in canonical_map.items():
                score = SequenceMatcher(None, norm, existing).ratio()
                if score > best_score:
                    best_score = score
                    best_match = canonical

            if best_match and best_score >= 0.80:
                canonical = best_match
            else:
                canonical = norm
                canonical_map[norm] = canonical

            res_copy = dict(res)
            res_copy["_run"] = run_idx + 1
            grouped[canonical].append(res_copy)

    return dict(grouped)


def print_resource_comparison(canonical: str, instances: list[dict]):
    runs = [inst["_run"] for inst in instances]
    print(f"\n  {'='*70}")
    print(f"  RESOURCE: {canonical}")
    print(f"  Appears in runs: {runs}")

    names = [inst.get("name", "") for inst in instances]
    if len(set(names)) > 1:
        print(f"\n  Names:")
        for inst in instances:
            print(f"    run {inst['_run']}: {inst['name']}")

    # Compare descriptions
    descs = [inst.get("description", "") for inst in instances]
    if len(set(descs)) == 1:
        print(f"\n  Description: IDENTICAL across {len(instances)} runs")
        d = descs[0]
        print(f"    \"{d[:120]}...\"" if len(d) > 120 else f"    \"{d}\"")
    else:
        sims = []
        for i in range(len(descs)):
            for j in range(i + 1, len(descs)):
                sims.append(SequenceMatcher(None, descs[i], descs[j]).ratio())
        avg_sim = sum(sims) / len(sims) if sims else 0
        print(f"\n  Description: VARIES (similarity={avg_sim:.3f})")
        for inst in instances:
            d = inst.get("description", "")
            preview = d[:150] + "..." if len(d) > 150 else d
            print(f"    run {inst['_run']}: \"{preview}\"")

    # Compare contact fields
    for field in ["phones", "addresses", "emails", "website"]:
        vals = [inst.get(field, [] if field != "website" else None) for inst in instances]

        normalized = []
        for v in vals:
            if isinstance(v, list):
                normalized.append(sorted(v))
            else:
                normalized.append(v)

        unique_strs = set(json.dumps(v, sort_keys=True) for v in normalized)
        if len(unique_strs) == 1:
            val = normalized[0]
            if val and val != []:
                print(f"\n  {field}: IDENTICAL = {val}")
        else:
            print(f"\n  {field}: VARIES")
            for inst in instances:
                print(f"    run {inst['_run']}: {inst.get(field, 'N/A')}")


def main():
    total = len(TEST_PROMPTS) * len(TEMPERATURES) * NUM_RUNS
    current = 0

    print(f"Resource Detail Comparison - PA/Keystone Region")
    print(f"Prompts: {len(TEST_PROMPTS)}, Temps: {TEMPERATURES}, Runs: {NUM_RUNS}")
    print(f"Total API calls: {total}")
    print("=" * 70)

    for prompt in TEST_PROMPTS:
        for temp in TEMPERATURES:
            runs_data: list[list[dict]] = []

            for run in range(1, NUM_RUNS + 1):
                current += 1
                sys.stdout.write(
                    f"\r[{current}/{total}] {prompt['label']} temp={temp} run={run}..."
                )
                sys.stdout.flush()

                start = time.time()
                result = call_api(prompt["query"], prompt["suffix"], temp)
                elapsed = time.time() - start
                resources = result.get("resources", [])
                runs_data.append(resources)
                print(
                    f"\r[{current}/{total}] {prompt['label']} temp={temp} run={run} "
                    f"-> {len(resources)} resources, {elapsed:.1f}s"
                )

            # Group and compare
            print(f"\n{'#'*70}")
            print(f"# {prompt['label']} | temp={temp}")
            print(f"{'#'*70}")

            grouped = group_resources_across_runs(runs_data)

            for canonical, instances in sorted(
                grouped.items(), key=lambda x: -len(x[1])
            ):
                print_resource_comparison(canonical, instances)

            # Summary stats
            print(f"\n  {'-'*70}")
            n_resources = [len(r) for r in runs_data]
            all_in_all = sum(1 for _, insts in grouped.items() if len(insts) == NUM_RUNS)
            print(f"  Resources per run: {n_resources}")
            print(f"  Resources appearing in ALL {NUM_RUNS} runs: {all_in_all}")

            if all_in_all > 0:
                desc_identical = 0
                phone_identical = 0
                addr_identical = 0
                web_identical = 0
                for _, insts in grouped.items():
                    if len(insts) != NUM_RUNS:
                        continue
                    descs = [i.get("description", "") for i in insts]
                    if len(set(descs)) == 1:
                        desc_identical += 1
                    phones = [json.dumps(sorted(i.get("phones", []))) for i in insts]
                    if len(set(phones)) == 1:
                        phone_identical += 1
                    addrs = [json.dumps(sorted(i.get("addresses", []))) for i in insts]
                    if len(set(addrs)) == 1:
                        addr_identical += 1
                    webs = [i.get("website") for i in insts]
                    if len(set(webs)) == 1:
                        web_identical += 1

                print(f"\n  Of {all_in_all} resources in all runs:")
                print(f"    Description identical: {desc_identical}/{all_in_all} ({desc_identical/all_in_all:.0%})")
                print(f"    Phones identical:      {phone_identical}/{all_in_all} ({phone_identical/all_in_all:.0%})")
                print(f"    Addresses identical:   {addr_identical}/{all_in_all} ({addr_identical/all_in_all:.0%})")
                print(f"    Website identical:     {web_identical}/{all_in_all} ({web_identical/all_in_all:.0%})")


if __name__ == "__main__":
    main()
