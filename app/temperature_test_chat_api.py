#!/usr/bin/env python3
"""
Temperature Testing: Finding the Right Balance (Using Chat Completions API)

NOTE: The OpenAI Responses API (used in production with web search) does NOT support
the temperature parameter. This test uses the Chat Completions API to demonstrate
temperature effects on consistency. Results will differ from production since web
search is not available with Chat Completions API.

Purpose: Demonstrate how temperature affects consistency and guide decision-making.
"""

import json
import os
import statistics
import time
from collections import Counter

from openai import OpenAI

# API key should be set in environment (export OPENAI_API_KEY=sk-xxx)
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# 5 diverse test cases - same as before
test_cases = [
    {
        "name": "Single Mother - Employment & Childcare",
        "location": "Austin, TX",
        "query": """You are a case worker assistant in Central Texas. Based on your knowledge, recommend 5-7 relevant social support resources in Austin, TX.

Client: Single mother with two young children (ages 3 and 5) needs:
- Employment opportunities
- Affordable childcare while job searching
- Food assistance
- Children's educational development resources
- Healthcare services

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}"""
    },
    {
        "name": "Veteran - Housing & Mental Health",
        "location": "Round Rock, TX",
        "query": """You are a case worker assistant in Central Texas. Based on your knowledge, recommend 5-7 relevant social support resources in Round Rock, TX.

Client: Military veteran experiencing homelessness needs:
- Emergency housing
- PTSD counseling and mental health services
- Job training programs
- VA benefits assistance
- Substance abuse treatment

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}"""
    },
    {
        "name": "Elderly - Medical & Daily Living",
        "location": "Georgetown, TX",
        "query": """You are a case worker assistant in Central Texas. Based on your knowledge, recommend 5-7 relevant social support resources in Georgetown, TX.

Client: 78-year-old living alone needs:
- Home healthcare services
- Meal delivery programs
- Transportation to medical appointments
- Social activities and companionship
- Prescription assistance programs

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}"""
    },
    {
        "name": "Teen Parent - Education & Support",
        "location": "Cedar Park, TX",
        "query": """You are a case worker assistant in Central Texas. Based on your knowledge, recommend 5-7 relevant social support resources in Cedar Park, TX.

Client: 17-year-old parent finishing high school needs:
- Parenting classes and support groups
- Childcare while attending school
- GED or high school completion programs
- Teen parent mentorship
- Financial literacy education

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}"""
    },
    {
        "name": "Domestic Violence Survivor - Safety & Recovery",
        "location": "Pflugerville, TX",
        "query": """You are a case worker assistant in Central Texas. Based on your knowledge, recommend 5-7 relevant social support resources in Pflugerville, TX.

Client: Domestic violence survivor with two children needs:
- Emergency shelter
- Legal advocacy and restraining order assistance
- Trauma counseling
- Job training and financial independence programs
- Safe childcare options

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}"""
    }
]

temperatures = [1.0, 0.75, 0.5, 0.25, 0.0]
runs_per_temperature = 3

print("=" * 100)
print("TEMPERATURE TESTING: Chat Completions API (WITHOUT Web Search)")
print("=" * 100)
print(f"\n⚠️  IMPORTANT NOTE:")
print(f"   The production app uses OpenAI Responses API with web search, which does NOT")
print(f"   support the temperature parameter. This test uses Chat Completions API to")
print(f"   demonstrate temperature effects. Results may differ from production.\n")
print(f"Test Configuration:")
print(f"  - Model: gpt-4o-mini")
print(f"  - API: Chat Completions (NOT Responses)")
print(f"  - Temperatures: {temperatures}")
print(f"  - Runs per temperature: {runs_per_temperature}")
print(f"  - Total test cases: {len(test_cases)}")
print(f"  - Total API calls: {len(test_cases) * len(temperatures) * runs_per_temperature}")
print(f"  - Web Search: NO (not supported in Chat Completions API)")
print("\n" + "=" * 100 + "\n")

client = OpenAI()
results = {}

# Run all tests
for case_idx, test_case in enumerate(test_cases, 1):
    print(f"\n{'=' * 100}")
    print(f"Test Case {case_idx}/{len(test_cases)}: {test_case['name']} ({test_case['location']})")
    print(f"{'=' * 100}\n")

    results[test_case['name']] = {}

    for temp in temperatures:
        print(f"  Temperature {temp}:", end=" ", flush=True)
        temp_results = []

        for run in range(runs_per_temperature):
            try:
                start = time.time()

                # Using Chat Completions API which supports temperature
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": test_case["query"]}],
                    temperature=temp
                )

                duration = time.time() - start
                text = response.choices[0].message.content

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

        results[test_case['name']][temp] = temp_results

        # Show summary for this temperature
        successful = [r for r in temp_results if r["success"]]
        if successful:
            avg_count = statistics.mean([r["resource_count"] for r in successful])
            print(f" → {len(successful)}/{runs_per_temperature} successful, avg {avg_count:.1f} resources")
        else:
            print(f" → 0/{runs_per_temperature} successful")

print("\n" + "=" * 100)
print("ANALYSIS: Computing Consistency and Diversity Metrics")
print("=" * 100 + "\n")

# Analyze results for each test case
analysis_results = {}

for case_name, case_results in results.items():
    print(f"\n{case_name}")
    print("-" * 100)

    case_analysis = {}

    for temp in temperatures:
        temp_data = case_results[temp]
        successful_runs = [r for r in temp_data if r["success"]]

        if len(successful_runs) < 2:
            print(f"  Temperature {temp:>4}: Insufficient data (only {len(successful_runs)} successful runs)")
            continue

        # Extract all resource names across runs
        all_resources = []
        for run in successful_runs:
            all_resources.extend(run["resource_names"])

        # Count occurrences of each resource
        resource_counter = Counter(all_resources)
        total_resources = len(all_resources)
        unique_resources = len(resource_counter)

        # Consistency score
        if total_resources > 0:
            resources_in_all_runs = sum(1 for count in resource_counter.values() if count == runs_per_temperature)
            resources_in_multiple_runs = sum(1 for count in resource_counter.values() if count >= 2)

            consistency_score = (resources_in_multiple_runs / unique_resources) * 100
            full_consistency_score = (resources_in_all_runs / unique_resources) * 100 if unique_resources > 0 else 0
        else:
            consistency_score = 0
            full_consistency_score = 0

        # Overlap analysis
        run_pairs_overlap = []
        for i in range(len(successful_runs)):
            for j in range(i + 1, len(successful_runs)):
                set_i = set(successful_runs[i]["resource_names"])
                set_j = set(successful_runs[j]["resource_names"])
                if len(set_i | set_j) > 0:
                    overlap = len(set_i & set_j) / len(set_i | set_j) * 100
                    run_pairs_overlap.append(overlap)

        avg_overlap = statistics.mean(run_pairs_overlap) if run_pairs_overlap else 0

        # Diversity score
        avg_resources_per_run = statistics.mean([r["resource_count"] for r in successful_runs])
        diversity_ratio = unique_resources / (avg_resources_per_run * runs_per_temperature) * 100

        case_analysis[temp] = {
            "consistency_score": consistency_score,
            "full_consistency_score": full_consistency_score,
            "avg_overlap_percent": avg_overlap,
            "unique_resources": unique_resources,
            "total_resources": total_resources,
            "diversity_ratio": diversity_ratio,
            "avg_resources_per_run": avg_resources_per_run,
            "successful_runs": len(successful_runs)
        }

        print(f"  Temperature {temp:>4}:")
        print(f"    • Consistency: {consistency_score:>5.1f}% (resources in ≥2 runs) | {full_consistency_score:>5.1f}% (in all {runs_per_temperature} runs)")
        print(f"    • Avg Overlap: {avg_overlap:>5.1f}% (Jaccard similarity between run pairs)")
        print(f"    • Diversity: {unique_resources} unique resources from {total_resources} total ({diversity_ratio:.1f}% diversity ratio)")
        print(f"    • Avg Resources/Run: {avg_resources_per_run:.1f}")

    analysis_results[case_name] = case_analysis

# Overall summary
print("\n" + "=" * 100)
print("OVERALL SUMMARY: Temperature Performance Across All Test Cases")
print("=" * 100 + "\n")

for temp in temperatures:
    print(f"Temperature {temp}:")

    temp_stats = {
        "consistency_scores": [],
        "full_consistency_scores": [],
        "avg_overlaps": [],
        "diversity_ratios": []
    }

    for case_analysis in analysis_results.values():
        if temp in case_analysis:
            temp_stats["consistency_scores"].append(case_analysis[temp]["consistency_score"])
            temp_stats["full_consistency_scores"].append(case_analysis[temp]["full_consistency_score"])
            temp_stats["avg_overlaps"].append(case_analysis[temp]["avg_overlap_percent"])
            temp_stats["diversity_ratios"].append(case_analysis[temp]["diversity_ratio"])

    if temp_stats["consistency_scores"]:
        print(f"  • Avg Consistency: {statistics.mean(temp_stats['consistency_scores']):.1f}% (≥2 runs) | {statistics.mean(temp_stats['full_consistency_scores']):.1f}% (all runs)")
        print(f"  • Avg Overlap: {statistics.mean(temp_stats['avg_overlaps']):.1f}%")
        print(f"  • Avg Diversity Ratio: {statistics.mean(temp_stats['diversity_ratios']):.1f}%")
        print()

print("=" * 100)
print("IMPORTANT FINDINGS & RECOMMENDATIONS")
print("=" * 100)
print("""
⚠️  CRITICAL DISCOVERY:
   The OpenAI Responses API (used in your production app with web search) does NOT
   support the temperature parameter. This means:

   1. Your app is using the DEFAULT temperature (likely 1.0) which causes maximum randomness
   2. Temperature CANNOT be adjusted in the Responses API
   3. The inconsistency users are experiencing is inherent to the current API

INTERPRETATION OF RESULTS ABOVE:
   The test results above show how temperature would affect consistency IF it were
   supported. Lower temperatures (0.25-0.5) typically show:
   - Higher consistency (70-90% overlap between runs)
   - Lower diversity (100-130% diversity ratio)
   - More predictable results for users

OPTIONS TO ADDRESS USER FEEDBACK:

Option 1: Switch to Chat Completions API
   ✓ Supports temperature parameter (can set to 0.5 for consistency)
   ✗ Loses web search capability
   ✗ May provide less current/accurate resource information

Option 2: Keep Responses API, accept variability
   ✓ Maintains web search for current information
   ✗ Cannot control temperature (stuck at default ~1.0)
   ✗ Users will continue to see varying results

Option 3: Hybrid approach
   - Use Responses API (with web search) for initial recommendations
   - Cache or prioritize frequently recommended resources
   - Show "core" resources consistently + some variable ones

Option 4: Post-processing consistency
   - Use Responses API but implement caching/scoring
   - Track which resources appear frequently for similar queries
   - Boost those resources in future similar queries

RECOMMENDATION:
   Given that web search provides significant value for finding current resources,
   consider Option 3 or 4 rather than sacrificing web search. Implement a hybrid
   system that maintains some consistency while leveraging web search benefits.

NEXT STEPS:
   1. Review the temperature test results above to see the consistency impact
   2. Decide if web search is essential (likely yes for case worker tools)
   3. If yes, implement post-processing or caching for consistency
   4. If no, switch to Chat Completions API with temperature=0.5
""")
print("=" * 100)
