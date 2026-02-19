#!/usr/bin/env python3
"""
Test if temperature parameter affects web search usage frequency.

Configuration:
- Model: gpt-5.1 (production model)
- Reasoning: none (current optimal config)
- Temperature: 0.0, 0.25, 0.5, 0.75, 1.0
- Test each temperature with 10 diverse prompts
- Track web search usage indicators

Hypothesis: Temperature may affect model's decision to invoke web search tool.
"""

import os
import json
import time
from openai import OpenAI
from collections import defaultdict

# Check for API key
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# 10 diverse test prompts covering different scenarios
TEST_PROMPTS = [
    "Single mother with 2 kids facing eviction in Austin, needs emergency housing assistance",
    "Homeless veteran in Travis County needs transitional housing and job training",
    "Low-income family with 4 children needs food assistance in Austin, TX",
    "Unemployed single parent needs job training and childcare assistance in Austin",
    "Uninsured family needs low-cost healthcare clinic in Austin, TX",
    "Working parent needs affordable childcare for toddler and preschooler in Austin",
    "Person recently laid off needs help applying for unemployment benefits in Texas",
    "Elderly couple on fixed income needs help with rising rent costs in Austin",
    "Ex-offender needs employment programs for people with criminal records in Travis County",
    "Person with substance abuse issues needs addiction treatment programs in Austin",
]

print("=" * 80)
print("TEMPERATURE vs WEB SEARCH USAGE ANALYSIS")
print("=" * 80)
print(f"Model: gpt-5.1")
print(f"Reasoning: none (optimal production config)")
print(f"Temperature values: 0.0, 0.25, 0.5, 0.75, 1.0")
print(f"Prompts per temperature: {len(TEST_PROMPTS)}")
print(f"Total tests: {len(TEST_PROMPTS) * 5} API calls")
print("=" * 80)
print("\nHypothesis: Temperature may affect how often the model invokes web search.")
print("=" * 80)

client = OpenAI()

def run_test(prompt_text: str, temperature: float, prompt_num: int, total_prompts: int) -> dict:
    """Run a single test with the given temperature."""

    # Format the prompt as the app would
    formatted_prompt = f"""You are a case worker assistant in Central Texas. Recommend 5-7 relevant social support resources.

Client: {prompt_text}

Return ONLY valid JSON in this exact format:
{{
  "resources": [
    {{
      "name": "Organization Name",
      "description": "Brief description",
      "website": "URL",
      "phones": ["phone number"],
      "emails": ["email"],
      "addresses": ["address"]
    }}
  ]
}}"""

    print(f"\n{'='*80}")
    print(f"Temperature {temperature} | Prompt {prompt_num}/{total_prompts}")
    print(f"Prompt: {prompt_text[:70]}...")
    print(f"{'='*80}")

    try:
        start_time = time.time()

        api_params = {
            "model": "gpt-5.1",
            "input": formatted_prompt,
            "reasoning": {"effort": "none"},
            "tools": [{"type": "web_search"}],
            "temperature": temperature
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
            resource_count = len(result_json.get("resources", []))
            resource_names = [r.get("name", "Unknown") for r in result_json.get("resources", [])]
        else:
            resource_count = 0
            resource_names = []
            result_json = None

        # Check for web search indicators in response (heuristic)
        web_search_indicators = [
            "according to",
            "based on",
            "website shows",
            "online information",
            "current information",
            "recently",
            "as of",
            ".org",
            ".gov",
            ".com",
            "http",
            "www.",
        ]

        response_lower = response_text.lower()
        indicators_found = [ind for ind in web_search_indicators if ind in response_lower]
        likely_used_web_search = len(indicators_found) >= 2  # Need at least 2 indicators

        # Count URLs in response (strong indicator of web search)
        url_count = response_text.count("http") + response_text.count(".org") + response_text.count(".gov")

        result = {
            "success": True,
            "temperature": temperature,
            "response_time": round(elapsed, 2),
            "resource_count": resource_count,
            "resource_names": resource_names,
            "likely_used_web_search": likely_used_web_search,
            "indicators_found": indicators_found,
            "url_count": url_count,
            "output_text": response_text,
            "output_json": result_json,
            "error": None
        }

        print(f"✅ SUCCESS!")
        print(f"⏱️  Response time: {elapsed:.2f}s")
        print(f"📊 Resources found: {resource_count}")
        print(f"🔍 Likely used web search: {'YES' if likely_used_web_search else 'NO'}")
        print(f"🔗 URL indicators: {url_count}")
        if indicators_found:
            print(f"📝 Web indicators: {', '.join(indicators_found[:3])}{'...' if len(indicators_found) > 3 else ''}")

        return result

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg[:150]}")

        return {
            "success": False,
            "temperature": temperature,
            "response_time": 0,
            "resource_count": 0,
            "resource_names": [],
            "likely_used_web_search": False,
            "indicators_found": [],
            "url_count": 0,
            "output_text": None,
            "output_json": None,
            "error": error_msg
        }

# Store all results
all_results = []
temperature_values = [0.0, 0.25, 0.5, 0.75, 1.0]

# Test each temperature with all prompts
for temp in temperature_values:
    print(f"\n{'#'*80}")
    print(f"# TESTING TEMPERATURE = {temp}")
    print(f"{'#'*80}")

    for i, prompt in enumerate(TEST_PROMPTS, 1):
        result = run_test(prompt, temp, i, len(TEST_PROMPTS))
        result["prompt"] = prompt
        all_results.append(result)

        # Small delay to avoid rate limits
        time.sleep(1)

print("\n" + "=" * 80)
print("ANALYSIS: Temperature Impact on Web Search Usage")
print("=" * 80)

# Aggregate statistics by temperature
temp_stats = {}
for temp in temperature_values:
    temp_results = [r for r in all_results if r["temperature"] == temp and r["success"]]

    if temp_results:
        web_search_count = sum(1 for r in temp_results if r["likely_used_web_search"])
        total_urls = sum(r["url_count"] for r in temp_results)
        avg_latency = sum(r["response_time"] for r in temp_results) / len(temp_results)
        avg_resources = sum(r["resource_count"] for r in temp_results) / len(temp_results)

        temp_stats[temp] = {
            "total_tests": len(temp_results),
            "web_search_count": web_search_count,
            "web_search_rate": (web_search_count / len(temp_results) * 100) if temp_results else 0,
            "total_url_indicators": total_urls,
            "avg_url_indicators": total_urls / len(temp_results) if temp_results else 0,
            "avg_latency": avg_latency,
            "avg_resources": avg_resources
        }

print("\n📊 RESULTS BY TEMPERATURE:\n")
for temp in temperature_values:
    if temp in temp_stats:
        stats = temp_stats[temp]
        print(f"Temperature {temp}:")
        print(f"  Tests: {stats['total_tests']}")
        print(f"  Web search usage: {stats['web_search_count']}/{stats['total_tests']} ({stats['web_search_rate']:.1f}%)")
        print(f"  Avg URL indicators: {stats['avg_url_indicators']:.1f}")
        print(f"  Avg latency: {stats['avg_latency']:.2f}s")
        print(f"  Avg resources: {stats['avg_resources']:.1f}")
        print()

print("=" * 80)
print("COMPARATIVE ANALYSIS")
print("=" * 80)

# Find temperature with highest web search usage
if temp_stats:
    max_ws_temp = max(temp_stats.keys(), key=lambda t: temp_stats[t]["web_search_rate"])
    min_ws_temp = min(temp_stats.keys(), key=lambda t: temp_stats[t]["web_search_rate"])

    print(f"\n🔝 HIGHEST web search usage: temperature={max_ws_temp}")
    print(f"   {temp_stats[max_ws_temp]['web_search_count']}/{temp_stats[max_ws_temp]['total_tests']} queries ({temp_stats[max_ws_temp]['web_search_rate']:.1f}%)")

    print(f"\n🔻 LOWEST web search usage: temperature={min_ws_temp}")
    print(f"   {temp_stats[min_ws_temp]['web_search_count']}/{temp_stats[min_ws_temp]['total_tests']} queries ({temp_stats[min_ws_temp]['web_search_rate']:.1f}%)")

    # Calculate difference
    diff = temp_stats[max_ws_temp]["web_search_rate"] - temp_stats[min_ws_temp]["web_search_rate"]
    print(f"\n📈 Difference: {diff:.1f} percentage points")

    if diff > 20:
        print(f"\n⚠️  SIGNIFICANT IMPACT: Temperature has a major effect on web search usage!")
        print(f"   Consider using temperature={max_ws_temp} to maximize web search")
    elif diff > 10:
        print(f"\n⚠️  MODERATE IMPACT: Temperature has a noticeable effect on web search usage")
        print(f"   Temperature={max_ws_temp} may improve web search frequency")
    else:
        print(f"\n✅ MINIMAL IMPACT: Temperature does not significantly affect web search usage")
        print(f"   Current temperature={0.25} is fine for web search frequency")

print("\n" + "=" * 80)
print("LATENCY vs WEB SEARCH TRADE-OFF")
print("=" * 80)

# Check if higher web search correlates with higher latency
ws_rates = [(t, temp_stats[t]["web_search_rate"], temp_stats[t]["avg_latency"])
            for t in temp_stats.keys()]
ws_rates.sort(key=lambda x: x[1], reverse=True)  # Sort by web search rate

print("\nRanked by web search usage:")
for temp, ws_rate, latency in ws_rates:
    print(f"  temp={temp}: {ws_rate:.1f}% web search, {latency:.2f}s avg latency")

print("\n" + "=" * 80)
print("KEY FINDINGS")
print("=" * 80)

# Summary findings
findings = []

# Finding 1: Overall web search rate
overall_ws_rate = sum(temp_stats[t]["web_search_count"] for t in temp_stats) / sum(temp_stats[t]["total_tests"] for t in temp_stats) * 100
findings.append(f"1. Overall web search usage: {overall_ws_rate:.1f}% of queries")

# Finding 2: Temperature impact
if diff > 10:
    findings.append(f"2. Temperature DOES affect web search: {diff:.1f}pp difference between extremes")
else:
    findings.append(f"2. Temperature does NOT significantly affect web search: only {diff:.1f}pp difference")

# Finding 3: Optimal temperature for web search
findings.append(f"3. Best temperature for web search: {max_ws_temp} ({temp_stats[max_ws_temp]['web_search_rate']:.1f}% usage)")

# Finding 4: Speed consideration
fastest_temp = min(temp_stats.keys(), key=lambda t: temp_stats[t]["avg_latency"])
findings.append(f"4. Fastest temperature: {fastest_temp} ({temp_stats[fastest_temp]['avg_latency']:.2f}s avg)")

for finding in findings:
    print(f"  {finding}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if diff > 20 and temp_stats[max_ws_temp]["avg_latency"] < temp_stats[0.25]["avg_latency"] * 1.2:
    print(f"✅ RECOMMENDATION: Switch to temperature={max_ws_temp}")
    print(f"   - {temp_stats[max_ws_temp]['web_search_rate']:.1f}% web search usage (vs {temp_stats[0.25]['web_search_rate']:.1f}% at current temp=0.25)")
    print(f"   - Acceptable latency impact")
elif diff > 10:
    print(f"⚠️  RECOMMENDATION: Consider temperature={max_ws_temp} for more web search usage")
    print(f"   - {temp_stats[max_ws_temp]['web_search_rate']:.1f}% web search usage")
    print(f"   - Test with real users to validate benefit")
else:
    print(f"✅ RECOMMENDATION: Keep current temperature=0.25")
    print(f"   - Temperature does not significantly affect web search frequency")
    print(f"   - Current config already provides {temp_stats[0.25]['web_search_rate']:.1f}% web search usage")

print("\n" + "=" * 80)
print("IMPORTANT NOTES")
print("=" * 80)
print("⚠️  This test uses HEURISTICS to detect web search usage:")
print("   - Looks for URL patterns (.org, .gov, .com, http)")
print("   - Looks for phrases like 'according to', 'based on', etc.")
print("   - Counts >= 2 indicators as likely web search")
print("\n⚠️  For ACCURATE web search counts, check your observability traces:")
print("   - Look for 'OpenAIWebSearch' component spans")
print("   - Check for 'web_search_...' child spans")
print("   - Verify 'websearch' tokens in span payloads")
print("\n⚠️  Manual trace inspection is REQUIRED to confirm these findings!")
print("=" * 80)

# Save detailed results
output_file = "temperature_websearch_analysis_results.json"
with open(output_file, "w") as f:
    json.dump({
        "metadata": {
            "model": "gpt-5.1",
            "reasoning": "none",
            "temperature_values": temperature_values,
            "prompts_per_temperature": len(TEST_PROMPTS),
            "total_tests": len(all_results)
        },
        "temperature_statistics": temp_stats,
        "detailed_results": all_results
    }, f, indent=2)

print(f"\n💾 Detailed results saved to: {output_file}")
print("\n" + "=" * 80)
