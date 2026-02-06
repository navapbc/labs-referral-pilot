#!/usr/bin/env python3
"""
Test if temperature parameter works with GPT-5.1 + reasoning="none" + web search
Team reports that 5.1 also supports temperature when reasoning is set to "none"
"""

import os
import json
import time
from openai import OpenAI

# Check for API key
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# Test query - single mother case
test_query = """You are a case worker assistant in Central Texas. Recommend 5-7 relevant social support resources.

Client: Single mother with two young children (ages 3 and 5) in Austin, TX needs:
- Employment opportunities
- Affordable childcare while job searching
- Food assistance

Return ONLY valid JSON in this exact format:
{
  "resources": [
    {
      "name": "Organization Name",
      "description": "Brief description",
      "website": "URL",
      "phones": ["phone number"],
      "emails": ["email"],
      "addresses": ["address"]
    }
  ]
}"""

print("=" * 80)
print("Testing GPT-5.1 with reasoning='none' for temperature support")
print("=" * 80)
print(f"Model: gpt-5.1")
print(f"Reasoning: none (KEY DIFFERENCE from earlier test!)")
print(f"Web Search: ENABLED")
print(f"Temperature values: 1.0, 0.75, 0.5, 0.25, 0.0")
print(f"Runs per temperature: 3 (to measure consistency)")
print("=" * 80)

client = OpenAI()

# Temperature values to test
temperatures = [1.0, 0.75, 0.5, 0.25, 0.0]

# Store all results
all_results = {}

for temp in temperatures:
    print(f"\n{'=' * 80}")
    print(f"TESTING TEMPERATURE = {temp}")
    print("=" * 80)

    temp_results = {
        "temperature": temp,
        "runs": [],
        "accepted": False,
        "error": None
    }

    # Run 3 times to measure consistency
    for run in range(1, 4):
        print(f"\nRun {run}/3 at temperature {temp}...")

        try:
            start_time = time.time()

            api_params = {
                "model": "gpt-5.1",  # Using 5.1 (not 5.2)
                "input": test_query,
                "reasoning": {"effort": "none"},  # Changed from "low" to "none"
                "tools": [{"type": "web_search"}],
                "temperature": temp
            }

            response = client.responses.create(**api_params)
            elapsed = time.time() - start_time

            # Parse response
            response_text = response.output_text

            # Extract JSON
            start = response_text.find("{")
            end = response_text.rfind("}")
            if start != -1 and end != -1:
                json_str = response_text[start:end + 1]
                result_json = json.loads(json_str)
                resource_names = [r.get("name", "Unknown") for r in result_json.get("resources", [])]
            else:
                resource_names = []

            temp_results["accepted"] = True
            temp_results["runs"].append({
                "run": run,
                "success": True,
                "response_time": round(elapsed, 2),
                "resource_count": len(resource_names),
                "resources": resource_names
            })

            print(f"  ✅ SUCCESS!")
            print(f"  ⏱️  Response time: {elapsed:.2f}s")
            print(f"  📊 Resources found: {len(resource_names)}")
            print(f"  📝 Resource names: {', '.join(resource_names[:3])}{'...' if len(resource_names) > 3 else ''}")

        except Exception as e:
            error_msg = str(e)
            temp_results["error"] = error_msg
            temp_results["runs"].append({
                "run": run,
                "success": False,
                "error": error_msg[:200]
            })

            if "temperature" in error_msg.lower() or "unsupported" in error_msg.lower():
                print(f"  ❌ REJECTED: Temperature not supported")
                print(f"  Error: {error_msg[:150]}")
                break  # No point trying more runs
            else:
                print(f"  ⚠️  Other error: {error_msg[:150]}")

    all_results[str(temp)] = temp_results

print("\n" + "=" * 80)
print("SUMMARY: Temperature Parameter Support")
print("=" * 80)

for temp in temperatures:
    result = all_results[str(temp)]
    if result["accepted"]:
        print(f"Temperature {temp}: ✅ ACCEPTED ({len(result['runs'])} successful runs)")
    else:
        print(f"Temperature {temp}: ❌ REJECTED")
        if result["error"]:
            print(f"  Error: {result['error'][:100]}")

print("\n" + "=" * 80)
print("CONSISTENCY ANALYSIS")
print("=" * 80)

for temp in temperatures:
    result = all_results[str(temp)]
    if not result["accepted"] or len(result["runs"]) < 2:
        print(f"\nTemperature {temp}: Insufficient data")
        continue

    # Calculate consistency metrics
    all_resources = []
    for run in result["runs"]:
        if run["success"]:
            all_resources.extend(run["resources"])

    # Count occurrences
    from collections import Counter
    resource_counts = Counter(all_resources)

    # Resources appearing in 2+ runs
    consistent_resources = [name for name, count in resource_counts.items() if count >= 2]

    # Resources appearing in all runs
    num_runs = len([r for r in result["runs"] if r["success"]])
    fully_consistent = [name for name, count in resource_counts.items() if count == num_runs]

    # Calculate overlap (Jaccard similarity between runs)
    overlaps = []
    runs = [r["resources"] for r in result["runs"] if r["success"]]
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            set1, set2 = set(runs[i]), set(runs[j])
            if len(set1 | set2) > 0:
                jaccard = len(set1 & set2) / len(set1 | set2)
                overlaps.append(jaccard)

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0

    # Calculate average response time
    avg_time = sum(r["response_time"] for r in result["runs"] if r["success"]) / num_runs if num_runs > 0 else 0

    print(f"\nTemperature {temp}:")
    print(f"  Runs: {num_runs}")
    print(f"  Avg response time: {avg_time:.2f}s")
    print(f"  Total unique resources: {len(resource_counts)}")
    print(f"  Resources in ≥2 runs: {len(consistent_resources)} ({len(consistent_resources)/len(resource_counts)*100:.1f}%)")
    print(f"  Resources in ALL runs: {len(fully_consistent)} ({len(fully_consistent)/len(resource_counts)*100:.1f}%)")
    print(f"  Avg overlap (Jaccard): {avg_overlap*100:.1f}%")

    if fully_consistent:
        print(f"  Fully consistent resources: {', '.join(fully_consistent)}")

print("\n" + "=" * 80)
print("SPEED COMPARISON")
print("=" * 80)

accepted_temps = [t for t in temperatures if all_results[str(t)]["accepted"]]
if accepted_temps:
    for temp in accepted_temps:
        result = all_results[str(temp)]
        successful_runs = [r for r in result["runs"] if r["success"]]
        if successful_runs:
            avg_time = sum(r["response_time"] for r in successful_runs) / len(successful_runs)
            print(f"Temperature {temp}: {avg_time:.2f}s average")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

rejected_temps = [t for t in temperatures if not all_results[str(t)]["accepted"]]

if len(accepted_temps) > 1:  # More than just 1.0
    print("✅ SUCCESS! GPT-5.1 with reasoning='none' SUPPORTS custom temperature values!")
    print(f"   Accepted temperatures: {accepted_temps}")
    print("\n🎯 HUGE WIN: Your production config can enable temperature WITHOUT changing model!")
    print("   - Keep GPT-5.1 (fast speed)")
    print("   - Just ensure reasoning={'effort': 'none'}")
    print("   - Set temperature=[any value 0.0-1.0]")
    print("\n📊 Benefits vs GPT-5.2:")
    print("   - No 60% speed penalty")
    print("   - Temperature control still works")
    print("   - Drop-in configuration change")

    # Find best temperature
    best_temp = None
    best_overlap = 0
    for temp in accepted_temps:
        result = all_results[str(temp)]
        if result["accepted"]:
            runs = [r["resources"] for r in result["runs"] if r["success"]]
            if len(runs) >= 2:
                overlaps = []
                for i in range(len(runs)):
                    for j in range(i + 1, len(runs)):
                        set1, set2 = set(runs[i]), set(runs[j])
                        if len(set1 | set2) > 0:
                            jaccard = len(set1 & set2) / len(set1 | set2)
                            overlaps.append(jaccard)
                if overlaps:
                    avg = sum(overlaps) / len(overlaps)
                    if avg > best_overlap:
                        best_overlap = avg
                        best_temp = temp

    if best_temp is not None:
        print(f"\n🏆 Recommended temperature: {best_temp} (best consistency: {best_overlap*100:.1f}% overlap)")

elif len(accepted_temps) == 1 and 1.0 in accepted_temps:
    print("❌ REJECTED: Only temperature=1.0 is accepted")
    print("   Your team's information may be incorrect for GPT-5.1")
    print("   Only GPT-5.2 with reasoning='none' supports custom temperature values")
else:
    print("❌ FAILED: API rejected all temperature values")

if rejected_temps:
    print(f"\n⚠️  Rejected temperatures: {rejected_temps}")

print("=" * 80)

# Save detailed results to file
output_file = "gpt51_temperature_none_verification_results.json"
with open(output_file, "w") as f:
    json.dump(all_results, f, indent=2)
print(f"\n💾 Detailed results saved to: {output_file}")
