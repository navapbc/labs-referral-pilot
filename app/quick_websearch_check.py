#!/usr/bin/env python3
"""
Quick web search check - looks at most recent 1000 spans
"""
import os
import httpx
from collections import defaultdict

PHOENIX_URL = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "https://localhost:6006")
PHOENIX_PROJECT_NAME = os.environ.get("PHOENIX_PROJECT_NAME", "default")
PHOENIX_API_KEY = os.environ.get("PHOENIX_API_KEY", "")

headers = {}
if PHOENIX_API_KEY:
    headers["Authorization"] = f"Bearer {PHOENIX_API_KEY}"

print("=" * 80)
print("QUICK WEB SEARCH CHECK (Recent 1000 spans)")
print("=" * 80)
print(f"Phoenix URL: {PHOENIX_URL}")
print(f"Project: {PHOENIX_PROJECT_NAME}")
print("=" * 80)

# Fetch first 1000 spans (10 pages)
print("\nFetching recent spans...")
all_spans = []
cursor = None

for page in range(1, 11):  # Get 10 pages = 1000 spans
    url = f"{PHOENIX_URL}/v1/projects/{PHOENIX_PROJECT_NAME}/spans"
    if cursor:
        url += f"?cursor={cursor}"

    response = httpx.get(url, headers=headers, verify=False, timeout=60.0)
    data = response.json()
    spans = data.get('data', [])
    all_spans.extend(spans)

    cursor = data.get('next_cursor')
    if not cursor or len(spans) == 0:
        break

print(f"Fetched {len(all_spans)} spans\n")

# Group by trace_id
traces = defaultdict(list)
for span in all_spans:
    trace_id = span.get('context', {}).get('trace_id', '')
    if trace_id:
        traces[trace_id].append(span)

print(f"Found {len(traces)} unique traces\n")

# Detect web search
def detect_web_search(trace_spans):
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
        return 'NO'

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

# Analyze traces
results = {'YES': 0, 'NO': 0, 'DISTANCE_ONLY': 0, 'N/A': 0}
generator_count = 0
search_call_count = 0

for trace_id, span_list in traces.items():
    result = detect_web_search(span_list)
    results[result] += 1

    for span in span_list:
        if span.get('name') == 'OpenAIWebSearchGenerator.run':
            generator_count += 1
        elif span.get('name') == 'web_search_call':
            search_call_count += 1

print("=" * 80)
print("RESULTS")
print("=" * 80)

total = len(traces)
print(f"\nWeb Search Usage (recent {total} traces):")
print(f"  ✅ YES (web search used):           {results['YES']:4d} ({results['YES']/total*100:5.1f}%)")
print(f"  ❌ NO (generator ran, no search):   {results['NO']:4d} ({results['NO']/total*100:5.1f}%)")
print(f"  📏 DISTANCE_ONLY:                   {results['DISTANCE_ONLY']:4d} ({results['DISTANCE_ONLY']/total*100:5.1f}%)")
print(f"  ⚪ N/A (no generator):               {results['N/A']:4d} ({results['N/A']/total*100:5.1f}%)")

print(f"\nSpan-level counts:")
print(f"  OpenAIWebSearchGenerator.run: {generator_count}")
print(f"  web_search_call:              {search_call_count}")

print("\n" + "=" * 80)

if results['YES'] > 0:
    print(f"✅ Web search IS being used in production")
    print(f"   {results['YES']} out of {total} traces used web search ({results['YES']/total*100:.1f}%)")
elif results['NO'] > 0:
    print(f"⚠️  Generator ran {results['NO']} times but web search was not invoked")
    print(f"   The LLM is choosing NOT to use the web search tool")
elif generator_count == 0:
    print(f"❌ No OpenAIWebSearchGenerator.run spans found")
    print(f"   Web search may not be configured in production")

print("=" * 80)
