#!/usr/bin/env python3
"""
Production-Realistic Temperature Test - CORRECTED VERSION
Uses GPT-5.1 (no reasoning) as specified by user, matching actual production usage.
Tests if temperature parameter is actually supported with Responses API + web search.
"""

import json
import os
import statistics
import time
from collections import Counter

from openai import OpenAI

# API key should be set in environment
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# Test case - single scenario run multiple times to measure consistency
test_case = {
    "name": "Single Mother - Employment & Childcare",
    "location": "Austin, TX",
    "query": """You are a case worker assistant in Central Texas. Recommend 5-7 relevant social support resources in Austin, TX.

Client: Single mother with two young children (ages 3 and 5) needs:
- Employment opportunities
- Affordable childcare while job searching
- Food assistance
- Children's educational development resources
- Healthcare services

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}"""
}

# Test configurations
temperatures = [1.0, 0.75, 0.5, 0.25, 0.0]
runs_per_temperature = 3
model = "gpt-5.1"  # CORRECTED: Using gpt-5.1 as user specified
reasoning_effort = "low"  # No reasoning / low effort

print("=" * 100)
print("PRODUCTION-REALISTIC TEMPERATURE TEST - CORRECTED")
print("=" * 100)
print(f"\nConfiguration (CORRECTED - using gpt-5.1):")
print(f"  - Model: {model} (gpt-5.1 no reasoning)")
print(f"  - API: OpenAI Responses API")
print(f"  - Web Search: ENABLED")
print(f"  - Reasoning Effort: {reasoning_effort} (no reasoning)")
print(f"  - Temperatures: {temperatures}")
print(f"  - Runs per temperature: {runs_per_temperature}")
print(f"  - Test case: {test_case['name']}")
print("\n" + "=" * 100 + "\n")

client = OpenAI()
results = {}

print("PHASE 1: Testing if Responses API accepts temperature parameter with gpt-5.1")
print("-" * 100)

# First, test if temperature parameter is even accepted
for temp in temperatures:
    print(f"\nTesting temperature={temp}...", end=" ")

    try:
        # Production-realistic API call with gpt-5.1
        api_params = {
            "model": model,
            "input": test_case["query"],
            "reasoning": {"effort": reasoning_effort},
            "tools": [{"type": "web_search"}],
            "temperature": temp  # TESTING: Can we add this parameter?
        }

        response = client.responses.create(**api_params)

        # Check what temperature the API actually used
        actual_temp = getattr(response, 'temperature', None)

        print(f"✅ ACCEPTED! API returned temperature={actual_temp}")

    except Exception as e:
        error_msg = str(e)
        if "temperature" in error_msg.lower() or "unexpected" in error_msg.lower() or "unsupported" in error_msg.lower():
            print(f"❌ REJECTED: {error_msg[:80]}")
        else:
            print(f"⚠️  Error (not temperature-related): {error_msg[:80]}")
        continue

print("\n" + "=" * 100)
print("PHASE 2: Consistency Testing at each temperature (if supported)")
print("=" * 100 + "\n")

# Now run full consistency tests
for temp in temperatures:
    print(f"\nTemperature {temp}:")
    print(f"  ", end="")

    temp_results = []

    for run in range(runs_per_temperature):
        try:
            start = time.time()

            # Production-realistic API call
            api_params = {
                "model": model,
                "input": test_case["query"],
                "reasoning": {"effort": reasoning_effort},
                "tools": [{"type": "web_search"}],
                "temperature": temp
            }

            response = client.responses.create(**api_params)
            duration = time.time() - start
            text = response.output_text

            # Parse JSON response
            try:
                start_idx = text.find('{')
                end_idx = text.rfind('}') + 1
                if start_idx != -1:
                    data = json.loads(text[start_idx:end_idx])
                    resource_names = [r.get("name", "") for r in data.get("resources", [])]
                else:
                    resource_names = []
            except:
                resource_names = []

            temp_results.append({
                "run": run + 1,
                "duration": duration,
                "resource_names": resource_names,
                "resource_count": len(resource_names),
                "success": True
            })

            print(f"✓", end="", flush=True)

        except Exception as e:
            temp_results.append({
                "run": run + 1,
                "duration": 0,
                "resource_names": [],
                "resource_count": 0,
                "success": False,
                "error": str(e)
            })
            print(f"✗", end="", flush=True)

    results[temp] = temp_results

    # Show summary
    successful = [r for r in temp_results if r["success"]]
    if successful:
        avg_count = statistics.mean([r["resource_count"] for r in successful])
        avg_time = statistics.mean([r["duration"] for r in successful])
        print(f" → {len(successful)}/{runs_per_temperature} successful, avg {avg_count:.1f} resources, {avg_time:.1f}s")
    else:
        print(f" → 0/{runs_per_temperature} successful")

# Analysis
print("\n" + "=" * 100)
print("CONSISTENCY ANALYSIS")
print("=" * 100 + "\n")

for temp in temperatures:
    temp_data = results.get(temp, [])
    successful_runs = [r for r in temp_data if r["success"]]

    if len(successful_runs) < 2:
        print(f"Temperature {temp}: Insufficient data")
        continue

    # Extract all resource names
    all_resources = []
    for run in successful_runs:
        all_resources.extend(run["resource_names"])

    # Count occurrences
    resource_counter = Counter(all_resources)
    total_resources = len(all_resources)
    unique_resources = len(resource_counter)

    # Calculate metrics
    if total_resources > 0:
        resources_in_all_runs = sum(1 for count in resource_counter.values() if count == runs_per_temperature)
        resources_in_multiple_runs = sum(1 for count in resource_counter.values() if count >= 2)

        consistency_score = (resources_in_multiple_runs / unique_resources) * 100 if unique_resources > 0 else 0
        full_consistency_score = (resources_in_all_runs / unique_resources) * 100 if unique_resources > 0 else 0
    else:
        consistency_score = 0
        full_consistency_score = 0

    # Overlap between runs
    run_pairs_overlap = []
    for i in range(len(successful_runs)):
        for j in range(i + 1, len(successful_runs)):
            set_i = set(successful_runs[i]["resource_names"])
            set_j = set(successful_runs[j]["resource_names"])
            if len(set_i | set_j) > 0:
                overlap = len(set_i & set_j) / len(set_i | set_j) * 100
                run_pairs_overlap.append(overlap)

    avg_overlap = statistics.mean(run_pairs_overlap) if run_pairs_overlap else 0

    # Diversity
    avg_resources_per_run = statistics.mean([r["resource_count"] for r in successful_runs])
    diversity_ratio = unique_resources / (avg_resources_per_run * runs_per_temperature) * 100

    print(f"Temperature {temp:>4}:")
    print(f"  • Consistency: {consistency_score:>5.1f}% (resources in ≥2 runs) | {full_consistency_score:>5.1f}% (in all runs)")
    print(f"  • Avg Overlap: {avg_overlap:>5.1f}% (Jaccard similarity)")
    print(f"  • Diversity: {unique_resources} unique from {total_resources} total ({diversity_ratio:.1f}% ratio)")
    print(f"  • Resources: {avg_resources_per_run:.1f} per run")
    print()

    # Show actual resource names for verification
    print(f"  Resources that appeared in all {runs_per_temperature} runs:")
    consistent_resources = [name for name, count in resource_counter.items() if count == runs_per_temperature]
    if consistent_resources:
        for res in consistent_resources:
            print(f"    - {res}")
    else:
        print(f"    (none)")
    print()

print("=" * 100)
print("CONCLUSIONS")
print("=" * 100)
print("""
This test uses the CORRECT production model:
- OpenAI Responses API (not Chat Completions)
- gpt-5.1 (NO reasoning)
- Web search enabled
- Reasoning effort: low

Key Questions Answered:
1. Does Responses API accept temperature parameter with gpt-5.1? (See Phase 1)
2. If yes, does it actually affect consistency? (See Phase 2 & Analysis)
3. What temperature gives best balance? (See consistency scores)

Next Steps:
- If temperature IS supported: Update src/common/components.py to add temperature parameter
- If temperature is NOT supported: Consider hybrid caching approach from TEMPERATURE_ANALYSIS_REPORT.md
""")
print("=" * 100)
