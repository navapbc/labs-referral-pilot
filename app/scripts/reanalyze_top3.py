#!/usr/bin/env python3
"""
Re-analyze temperature experiment: consistency of the FIRST 3 resources returned.

Uses fuzzy matching + considers only the first 3 resources in original order.
Two metrics:
  1. Set consistency (Jaccard) - are the same 3 resources in the top 3, regardless of order?
  2. Order consistency - are the same 3 resources in the same order?
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher

RAW_CSV = "app/scripts/temp_experiment_raw_20260217_101416.csv"
TOP_N = 3


def normalize_name(name: str) -> str:
    normalized = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    normalized = re.sub(r"\s*[–-]\s*$", "", normalized).strip()
    normalized = normalized.replace("–", "-").replace("—", "-")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def fuzzy_group(names: list[str], threshold: float = 0.80) -> dict[str, str]:
    canonical_map: dict[str, str] = {}
    original_to_canonical: dict[str, str] = {}

    for original_name in names:
        normalized = normalize_name(original_name)
        best_match = None
        best_score = 0.0

        for existing_norm, canonical in canonical_map.items():
            score = SequenceMatcher(None, normalized, existing_norm).ratio()
            if score > best_score:
                best_score = score
                best_match = canonical

        if best_match and best_score >= threshold:
            original_to_canonical[original_name] = best_match
        else:
            canonical_map[normalized] = normalized
            original_to_canonical[original_name] = normalized

    return original_to_canonical


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def main():
    with open(RAW_CSV) as f:
        rows = list(csv.DictReader(f))

    # Build fuzzy map from all names
    all_names = []
    for row in rows:
        if row["resource_names"]:
            all_names.extend(row["resource_names"].split("; "))
    name_map = fuzzy_group(list(set(all_names)), threshold=0.80)

    # Group runs by (label, temp), keeping original order and taking first N
    runs_by_key: dict[tuple, list] = defaultdict(list)
    for row in rows:
        if row["error"]:
            continue
        label = row["label"]
        temp = float(row["temperature"])
        raw_names = row["resource_names"].split("; ") if row["resource_names"] else []
        canonical = [name_map.get(n, normalize_name(n)) for n in raw_names]
        top_n = canonical[:TOP_N]
        runs_by_key[(label, temp)].append(top_n)

    temperatures = [0.0, 0.3, 0.6, 0.9]
    labels = ["housing-austin", "employment-austin", "rent-assist-austin", "dental-reading"]

    # --- Per-prompt detail ---
    print(f"=== TOP-{TOP_N} RESOURCE CONSISTENCY (fuzzy-matched) ===\n")

    summary = []
    for label in labels:
        print(f"--- {label} ---\n")
        for temp in temperatures:
            runs = runs_by_key.get((label, temp), [])
            if not runs:
                continue

            # Set-based Jaccard (order-independent)
            sets = [frozenset(r) for r in runs]
            jaccards = []
            for i in range(len(sets)):
                for j in range(i + 1, len(sets)):
                    jaccards.append(jaccard(sets[i], sets[j]))
            avg_jac = sum(jaccards) / len(jaccards) if jaccards else 1.0
            min_jac = min(jaccards) if jaccards else 1.0

            # Set exact match
            set_counter = Counter(sets)
            set_exact = set_counter.most_common(1)[0][1] / len(runs)

            # Order exact match (same resources in same positions)
            tuples = [tuple(r) for r in runs]
            order_counter = Counter(tuples)
            order_exact = order_counter.most_common(1)[0][1] / len(runs)

            summary.append({
                "label": label,
                "temp": temp,
                "avg_jaccard": avg_jac,
                "min_jaccard": min_jac,
                "set_exact": set_exact,
                "order_exact": order_exact,
            })

            print(f"  temp={temp:.1f}:")
            for i, run in enumerate(runs):
                print(f"    run {i+1}: {' | '.join(run)}")
            print(
                f"    -> set_jaccard={avg_jac:.3f} (min={min_jac:.3f}), "
                f"set_exact={set_exact:.0%}, order_exact={order_exact:.0%}"
            )
            print()
        print()

    # --- Summary table ---
    print("=" * 85)
    print(f"{'Label':<25} {'Temp':>5} {'SetJac':>7} {'MinJac':>7} {'SetExact':>9} {'OrdExact':>9}")
    print("-" * 85)

    current_label = ""
    for row in summary:
        if row["label"] != current_label:
            if current_label:
                print()
            current_label = row["label"]
        print(
            f"{row['label']:<25} {row['temp']:>5.1f} "
            f"{row['avg_jaccard']:>7.3f} {row['min_jaccard']:>7.3f} "
            f"{row['set_exact']:>8.0%} {row['order_exact']:>8.0%}"
        )

    # --- Cross-temp averages ---
    print()
    print("=" * 85)
    print("TEMPERATURE AVERAGES (across all prompts)")
    print("=" * 85)
    print()
    print(f"  {'Temp':>5} {'SetJac':>8} {'MinJac':>8} {'SetExact':>9} {'OrdExact':>9}")
    print(f"  {'-'*40}")

    for temp in temperatures:
        t_rows = [r for r in summary if r["temp"] == temp]
        if not t_rows:
            continue
        n = len(t_rows)
        print(
            f"  {temp:>5.1f} "
            f"{sum(r['avg_jaccard'] for r in t_rows)/n:>8.3f} "
            f"{sum(r['min_jaccard'] for r in t_rows)/n:>8.3f} "
            f"{sum(r['set_exact'] for r in t_rows)/n:>8.0%} "
            f"{sum(r['order_exact'] for r in t_rows)/n:>8.0%}"
        )


if __name__ == "__main__":
    main()
