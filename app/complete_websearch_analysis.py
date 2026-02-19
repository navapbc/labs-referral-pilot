#!/usr/bin/env python3
"""
Complete web search analysis - fetches ALL spans and analyzes them.
"""
import os
import httpx
from collections import defaultdict, Counter

PHOENIX_URL = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "https://localhost:6006")
PHOENIX_PROJECT_NAME = os.environ.get("PHOENIX_PROJECT_NAME", "default")
PHOENIX_API_KEY = os.environ.get("PHOENIX_API_KEY", "")

print("=" * 80)
print("COMPLETE WEB SEARCH ANALYSIS")
print("=" * 80)
print(f"Phoenix URL: {PHOENIX_URL}")
print(f"Project: {PHOENIX_PROJECT_NAME}")
print("=" * 80)

headers = {}
if PHOENIX_API_KEY:
    headers["Authorization"] = f"Bearer {PHOENIX_API_KEY}"

# Fetch ALL spans (no date filter)
print("\n🔍 Fetching all spans...")
all_spans = []
cursor = None
page = 0

while True:
    page += 1
    url = f"{PHOENIX_URL}/v1/projects/{PHOENIX_PROJECT_NAME}/spans"
    if cursor:
        url += f"?cursor={cursor}"

    response = httpx.get(url, headers=headers, verify=False, timeout=60.0)
    data = response.json()
    spans = data.get('data', [])

    all_spans.extend(spans)
    print(f"  Page {page}: {len(spans)} spans (total: {len(all_spans)})")

    cursor = data.get('next_cursor')
    if not cursor or len(spans) == 0:
        break

print(f"✅ Total spans fetched: {len(all_spans)}\n")

# Group by trace_id
traces = defaultdict(list)
for span in all_spans:
    trace_id = span.get('context', {}).get('trace_id', '')
    if trace_id:
        traces[trace_id].append(span)

print(f"📊 Total unique traces: {len(traces)}\n")

# Analyze web search usage
def detect_web_search(trace_spans):
    """Returns: YES, NO, DISTANCE_ONLY, N/A"""
    has_generator = False
    web_search_calls = []

    for span in trace_spans:
        name = span.get('name', '')
        if name == 'OpenAIWebSearchGenerator.run':
            has_generator = True
        elif name == 'web_search_call':
            web_search_calls.append(span)

    if not has_generator and not web_search_calls:
        return 'N/A'

    if not web_search_calls:
        return 'NO'  # Generator ran but LLM chose not to search

    # Classify search calls
    has_real_search = False
    has_distance = False

    for span in web_search_calls:
        attrs = span.get('attributes', {})
        action_type = attrs.get('action_type', '') or attrs.get('tool.parameters.action_type', '')
        query = str(attrs.get('query', '') or attrs.get('tool.parameters.query', ''))
        source_urls = attrs.get('source_urls', '') or attrs.get('tool.parameters.source_urls', '')

        if action_type == 'search' and source_urls:
            has_real_search = True
        elif query.startswith('calculator:') and 'distance' in query:
            has_distance = True
        elif query and not query.startswith('calculator'):
            has_real_search = True

    if has_real_search:
        return 'YES'
    if has_distance:
        return 'DISTANCE_ONLY'
    return 'NO'

# Analyze all traces
results = {'YES': 0, 'NO': 0, 'DISTANCE_ONLY': 0, 'N/A': 0}
generator_count = 0
search_call_count = 0

for trace_id, span_list in traces.items():
    result = detect_web_search(span_list)
    results[result] += 1

    # Count generators and search calls
    for span in span_list:
        if span.get('name') == 'OpenAIWebSearchGenerator.run':
            generator_count += 1
        elif span.get('name') == 'web_search_call':
            search_call_count += 1

print("=" * 80)
print("WEB SEARCH USAGE ANALYSIS")
print("=" * 80)

total_traces = len(traces)
print(f"\n📈 Results breakdown:")
print(f"  ✅ YES (web search used):           {results['YES']:4d} traces ({results['YES']/total_traces*100:5.1f}%)")
print(f"  ❌ NO (generator ran, no search):   {results['NO']:4d} traces ({results['NO']/total_traces*100:5.1f}%)")
print(f"  📏 DISTANCE_ONLY:                   {results['DISTANCE_ONLY']:4d} traces ({results['DISTANCE_ONLY']/total_traces*100:5.1f}%)")
print(f"  ⚪ N/A (no generator):               {results['N/A']:4d} traces ({results['N/A']/total_traces*100:5.1f}%)")

print(f"\n🔍 Span-level counts:")
print(f"  OpenAIWebSearchGenerator.run spans: {generator_count}")
print(f"  web_search_call spans:              {search_call_count}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if results['YES'] == 0 and results['NO'] > 0:
    print("\n❌ **WEB SEARCH IS NOT BEING USED IN PRODUCTION**")
    print(f"\n   Evidence:")
    print(f"   - Generator ran {results['NO']} times")
    print(f"   - BUT: 0 web_search_call spans found")
    print(f"   - This means the LLM is choosing NOT to use the web search tool")
    print(f"\n   Root cause:")
    print(f"   - Web search tool IS configured (generator spans exist)")
    print(f"   - But the LLM determines it doesn't need web search for these queries")
    print(f"   - OR: Phoenix instrumentation isn't capturing web_search_call spans")
    print(f"\n   Next steps:")
    print(f"   1. Check if using OpenAI Responses API (not captured by Phoenix)")
    print(f"   2. Try switching to Chat Completions API if compatible")
    print(f"   3. Add custom logging to verify web search invocations")
elif results['YES'] > 0:
    print(f"\n✅ Web search IS being used in {results['YES']} traces")
    print(f"   However, {results['NO']} traces had generator but no search")
else:
    print(f"\n⚪ No OpenAIWebSearchGenerator.run spans found at all")
    print(f"   The web search component may not be configured in production")

print("=" * 80)
