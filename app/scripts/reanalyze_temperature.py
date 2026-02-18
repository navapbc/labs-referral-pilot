#!/usr/bin/env python3
"""
Re-analyze temperature experiment results with fuzzy name matching.

Resource names like "Caritas of Austin – Housing Programs" and
"Caritas of Austin – Housing Programs (Rapid Rehousing & Supportive Housing)"
should count as the same resource.

Approach: Normalize names by stripping parenthetical suffixes, then use
difflib.SequenceMatcher for fuzzy grouping of remaining variations.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher

RAW_CSV = "app/scripts/temp_experiment_raw_20260217_101416.csv"


def normalize_name(name: str) -> str:
    """Normalize a resource name for fuzzy comparison.

    Steps:
    1. Strip trailing parenthetical details (the main source of variation)
    2. Normalize whitespace and dashes
    3. Lowercase
    """
    # Remove content in parentheses at the end, but keep the core name
    # e.g. "Caritas of Austin – Housing Programs (Rapid Rehousing & Supportive Housing)"
    #   -> "Caritas of Austin – Housing Programs"
    normalized = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    # Also strip trailing " –" or " -" left over
    normalized = re.sub(r"\s*[–-]\s*$", "", normalized).strip()
    # Normalize various dashes to standard dash
    normalized = normalized.replace("–", "-").replace("—", "-")
    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def fuzzy_group(names: list[str], threshold: float = 0.80) -> dict[str, str]:
    """Group similar normalized names together.

    Returns a mapping from original_name -> canonical_name.
    Uses greedy clustering: for each name, find the best match among
    existing canonical names. If similarity >= threshold, merge; otherwise
    create a new canonical name.
    """
    canonical_map: dict[str, str] = {}  # normalized -> canonical
    original_to_canonical: dict[str, str] = {}  # original -> canonical

    for original_name in names:
        normalized = normalize_name(original_name)

        # Check if we already have a close match
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
            # New canonical name - use the normalized form
            canonical_map[normalized] = normalized
            original_to_canonical[original_name] = normalized

    return original_to_canonical


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def compute_metrics(runs: list[list[str]]) -> dict:
    """Compute consistency metrics across runs of canonical names."""
    if not runs:
        return {}

    sets = [frozenset(r) for r in runs]

    jaccards = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            jaccards.append(jaccard_similarity(sets[i], sets[j]))

    counter = Counter(sets)
    most_common_count = counter.most_common(1)[0][1] if counter else 0
    exact_match_rate = most_common_count / len(runs)

    all_resources = set()
    for r in runs:
        all_resources.update(r)

    return {
        "avg_jaccard": sum(jaccards) / len(jaccards) if jaccards else 1.0,
        "min_jaccard": min(jaccards) if jaccards else 1.0,
        "exact_match_rate": exact_match_rate,
        "avg_count": sum(len(r) for r in runs) / len(runs),
        "unique_resources": len(all_resources),
        "all_resources": sorted(all_resources),
    }


def main():
    # Load raw data
    with open(RAW_CSV) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Collect all resource names across the entire dataset
    all_names = []
    for row in rows:
        if row["resource_names"]:
            all_names.extend(row["resource_names"].split("; "))

    print(f"Total raw resource name occurrences: {len(all_names)}")
    print(f"Unique raw names: {len(set(all_names))}")

    # Build fuzzy mapping
    name_map = fuzzy_group(list(set(all_names)), threshold=0.80)
    canonical_names = set(name_map.values())
    print(f"Canonical names after fuzzy grouping: {len(canonical_names)}")

    # Show the groupings for inspection
    print("\n=== FUZZY GROUPINGS ===\n")
    groups: dict[str, list[str]] = defaultdict(list)
    for original, canonical in sorted(name_map.items(), key=lambda x: x[1]):
        groups[canonical].append(original)

    for canonical, originals in sorted(groups.items()):
        if len(originals) > 1:
            print(f"  CANONICAL: {canonical}")
            for orig in sorted(originals):
                print(f"    <- {orig}")
            print()

    # Re-analyze with canonical names
    # Group runs by (label, temperature)
    runs_by_key: dict[tuple, list[list[str]]] = defaultdict(list)
    for row in rows:
        label = row["label"]
        temp = float(row["temperature"])
        if row["error"]:
            continue
        raw_names = row["resource_names"].split("; ") if row["resource_names"] else []
        canonical = [name_map.get(n, normalize_name(n)) for n in raw_names]
        runs_by_key[(label, temp)].append(canonical)

    # Print results
    temperatures = [0.0, 0.3, 0.6, 0.9]
    labels = ["housing-austin", "employment-austin", "rent-assist-austin", "dental-reading"]

    print("=" * 80)
    print("=== FUZZY-MATCHED CONSISTENCY RESULTS ===")
    print("=" * 80)
    print()
    print(
        f"{'Label':<25} {'Temp':>5} {'AvgRes':>7} {'Unique':>7} "
        f"{'Jaccard':>8} {'MinJac':>7} {'Exact%':>7}"
    )
    print("-" * 70)

    summary_rows = []
    current_label = ""
    for label in labels:
        for temp in temperatures:
            key = (label, temp)
            runs = runs_by_key.get(key, [])
            if not runs:
                continue
            metrics = compute_metrics(runs)

            if label != current_label:
                if current_label:
                    print()
                current_label = label

            print(
                f"{label:<25} {temp:>5.1f} "
                f"{metrics['avg_count']:>7.1f} "
                f"{metrics['unique_resources']:>7} "
                f"{metrics['avg_jaccard']:>8.3f} "
                f"{metrics['min_jaccard']:>7.3f} "
                f"{metrics['exact_match_rate']:>6.0%}"
            )
            summary_rows.append(
                {"label": label, "temp": temp, **metrics}
            )

    # Cross-temperature comparison
    print()
    print("=" * 80)
    print("=== TEMPERATURE COMPARISON (averaged across prompts) ===")
    print("=" * 80)
    print()

    for temp in temperatures:
        temp_rows = [r for r in summary_rows if r["temp"] == temp]
        if not temp_rows:
            continue
        avg_jac = sum(r["avg_jaccard"] for r in temp_rows) / len(temp_rows)
        avg_min = sum(r["min_jaccard"] for r in temp_rows) / len(temp_rows)
        avg_exact = sum(r["exact_match_rate"] for r in temp_rows) / len(temp_rows)
        avg_unique = sum(r["unique_resources"] for r in temp_rows) / len(temp_rows)
        print(
            f"  temp={temp:.1f}: "
            f"avg_jaccard={avg_jac:.3f}, "
            f"min_jaccard={avg_min:.3f}, "
            f"exact_match={avg_exact:.0%}, "
            f"avg_unique={avg_unique:.1f}"
        )

    # Per-prompt detail: show which resources appear in which runs
    print()
    print("=" * 80)
    print("=== PER-PROMPT RESOURCE FREQUENCY (across all temps & runs) ===")
    print("=" * 80)

    for label in labels:
        print(f"\n--- {label} ---")
        all_canonical = Counter()
        total_runs = 0
        for temp in temperatures:
            key = (label, temp)
            for run in runs_by_key.get(key, []):
                total_runs += 1
                for name in run:
                    all_canonical[name] += 1

        for name, count in all_canonical.most_common():
            pct = count / total_runs * 100
            bar = "█" * int(pct / 5)
            print(f"  {pct:5.0f}% ({count:2d}/{total_runs}) {bar} {name}")


if __name__ == "__main__":
    main()
