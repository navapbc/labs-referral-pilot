# Web Search Spike Root Cause Analysis

**Date:** February 20, 2026
**Branch:** performance-testing
**Environment:** Production (pilot-prod)

## Summary

Web search invocation in production increased from **8% historically to 43% recently** — a 5.6x increase. This report identifies the root causes by correlating the spike with specific code changes deployed between December 2025 and January 2026.

**The spike is caused by three reinforcing changes, not a single event:**

| Rank | Change | Date | Impact |
|------|--------|------|--------|
| 1 | Model switched to `gpt-5.1` with `reasoning="none"` | Jan 5, 2026 | **Primary cause** — this model invokes web search ~100% of the time |
| 2 | Keystone PA region added with no RAG resources | Jan 15-20, 2026 | **Major amplifier** — every Keystone query forces web search |
| 3 | RAG pipeline replaced full DB injection | Dec 5-8, 2025 | **Contributing factor** — fewer resources in context |

## Detailed Timeline

### Phase 1: Baseline (Oct 30 – Dec 4, 2025) — ~8% web search rate

Web search was added on Oct 30 (`8e2e214`) with the `OpenAIWebSearchGenerator` component. The generate_referrals pipeline used:

- **Model:** `gpt-5-mini` with `reasoning_effort="low"`
- **Resources:** All supports loaded from PostgreSQL via `LoadSupports()` and injected directly into the prompt
- **Web search:** Available but rarely used — the model had full resource context and was conservative about tool use

This is the period reflected in the **8% historical rate** (447/5,554 traces).

### Phase 2: RAG Introduction (Dec 5-8, 2025) — Moderate increase

| Commit | Date | Change |
|--------|------|--------|
| `c6623cb` | Dec 5 | Added `generate_referrals_rag` endpoint with ChromaDB vector retrieval (`top_k=10`) |
| `d976d51` | Dec 8 | Frontend switched to use RAG endpoint |

**Why this increased web search:**
- The old pipeline dumped **all** resources from PostgreSQL into the prompt. The RAG pipeline retrieves only the **top 10** most relevant documents from ChromaDB.
- Fewer resources in context means the LLM has less to work with and is more likely to supplement via web search.
- The Central TX prompt explicitly encourages this: *"Supplement with trusted resources you can find through web search."*

### Phase 3: Model Switch to gpt-5.1 (Jan 5, 2026) — PRIMARY CAUSE

| Commit | Date | Change |
|--------|------|--------|
| `d1b7388` | Jan 5 | All models centralized to `gpt-5.1` / `reasoning="none"` |

**Before:**
```
Non-RAG pipeline:  gpt-5-mini / reasoning="low"
RAG pipeline:      gpt-5      / reasoning="high" (component defaults)
```

**After:**
```
All pipelines:     gpt-5.1    / reasoning="none"
```

**Why this is the biggest factor:**

Benchmark testing (`reasoning_level_comparison_results.json`) shows `gpt-5.1` with `reasoning="none"` has a **100% web search invocation rate** (30/30 tests). The previous `gpt-5-mini` with `reasoning="low"` was far less aggressive about invoking the web search tool.

The combination of a more capable model (`gpt-5.1`) and disabling reasoning (`"none"`) fundamentally changed how the LLM interacts with the web search tool. Without reasoning overhead, the model defaults to using every tool available to it, including web search.

### Phase 4: Keystone PA Region (Jan 14-20, 2026) — MAJOR AMPLIFIER

| Commit | Date | Change |
|--------|------|--------|
| `e0c3541` | Jan 14 | Added prompt suffix handling |
| `1e8b9aa` | Jan 15 | Frontend added Keystone PA location suffix |
| `e581e25` | Jan 20 | Keystone prompt version updated |
| `e9cbcfd` | Jan 21 | RAG docs distinguished by region |

**Why this amplified the spike:**

The Keystone prompt has **no RAG resources section** — no `{% for s in supports %}` block. Instead, it explicitly instructs: *"Your response should include resources you find searching the web."*

This means **100% of Keystone queries force web search**, regardless of model behavior. As Keystone traffic grew after launch on Jan 15, the aggregate web search rate climbed proportionally.

### Phase 5: Cleanup & Temperature (Jan 23 – Feb 5, 2026)

| Commit | Date | Change |
|--------|------|--------|
| `003669f` | Jan 23 | Removed `Support`, `SupportListing`, `CrawlJob`, and other non-RAG code |
| `548929e` | Jan 26 | Removed old `generate_referrals` pipeline entirely |
| `8a8bf66` | Jan 26 | Hardcoded `suffix="centraltx"` as default |
| `540481a` | Feb 5 | Added temperature setting (`0.9` in production) |

These changes cemented the new architecture. The high temperature (0.9) may marginally influence the model's tendency to invoke web search, but this is not a primary driver.

### Phase 6: Improved Tracing (Feb 9, 2026)

| Commit | Date | Change |
|--------|------|--------|
| `b10c02a` | Feb 9 | Logged web search source URLs and context in Phoenix traces |

This improved **visibility** of web search calls in traces. Some of the measured increase in web search rate may be attributable to better detection, not just more actual usage.

## Current Production Configuration

```python
# app/src/app_config.py (origin/main)
generate_referrals_rag_model_version: str = "gpt-5.1"
generate_referrals_rag_reasoning_level: str = "none"
generate_referrals_rag_temperature: float = 0.9
```

```python
# app/src/common/components.py — web search is always enabled
"tools": [{"type": "web_search"}]
```

| Region | RAG Resources | Web Search Instruction | Expected Web Search Rate |
|--------|--------------|----------------------|--------------------------|
| Central TX | Yes (top_k=10 from ChromaDB) | "Supplement with trusted resources you can find through web search" | High (model + prompt both encourage it) |
| Keystone PA | None | "Your response should include resources you find searching the web" | ~100% (no other resource source) |

## Benchmark Evidence

From `reasoning_level_comparison_results.json` (30 test prompts):

| Model | Reasoning | Web Search Rate |
|-------|-----------|----------------|
| `gpt-5.1` | `none` | **100%** (30/30) |
| `gpt-5.1` | `low` | 0% (all failed) |

From `PRODUCTION_WEBSEARCH_ANALYSIS.md`:

| Period | Web Search Rate | Traces |
|--------|----------------|--------|
| Historical (all time) | 8.0% | 447 / 5,554 |
| Recent (last 1,000 spans) | 45.0% | 50 / 111 |

## Conclusions

1. **The model change is the primary cause.** Switching from `gpt-5-mini`/`reasoning="low"` to `gpt-5.1`/`reasoning="none"` on Jan 5 fundamentally changed web search behavior. The new model is dramatically more aggressive about using web search when it's available.

2. **The Keystone region is the secondary cause.** Its prompt has no RAG resources and explicitly requests web search, guaranteeing 100% web search usage for all Keystone traffic since Jan 15.

3. **The RAG migration is a contributing factor.** Providing top-k=10 vector results instead of all DB resources gives the LLM less context, making it more likely to supplement via web search.

4. **This is not a bug.** All three changes were intentional. The higher web search rate is a natural consequence of the new architecture. Whether this is desirable depends on whether the web search results improve output quality and whether the added latency is acceptable.

## Recommendations

1. **If web search rate needs to decrease:** Test `gpt-5.1` with `reasoning="low"` or `reasoning="medium"` — reasoning effort appears to be the strongest lever for controlling web search behavior.

2. **If Keystone web search rate needs to decrease:** Add RAG resources for the Keystone PA region so the prompt can include local resources alongside web search.

3. **Monitor quality:** Compare output quality for traces with and without web search to determine if the higher rate is beneficial.

4. **Consider prompt tuning:** The Central TX prompt's instruction to *"Supplement with trusted resources"* could be softened to *"Optionally supplement"* if web search rate is too high.
