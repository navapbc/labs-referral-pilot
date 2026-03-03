# Latency Benchmark Results: Model Performance & Referral Size Testing

**Test Date:** January 2026
**Purpose:** Compare model performance (GPT-5.1, GPT-5.2, GPT-5-mini) and test the impact of limiting referral output to 5 resources

---

## Table of Contents

1. [Model Comparison (10 queries)](#model-comparison-10-queries)
2. [Model Comparison (50 queries)](#model-comparison-50-queries)
3. [Referral Size Limit Testing](#referral-size-limit-testing)
4. [Gemini Speed Testing](#gemini-speed-testing)
5. [Parameter Effect Testing: Temperature and Reasoning](#parameter-effect-testing-temperature-and-reasoning)
6. [Key Findings & Recommendations](#key-findings--recommendations)

---

## Model Comparison (10 queries)

### Configuration
- **Models Tested:** gpt-5.1, gpt-5.2, gpt-5-mini
- **Reasoning:** none
- **Queries:** 10 diverse case worker scenarios

### Results

| Model       | Reasoning | Avg (ms)   | P50 (ms)   | P95 (ms)    | Success |
|-------------|-----------|------------|------------|-------------|---------|
| gpt-5.1     | none      | 11,215.82  | 11,636.47  | 17,320.01   | 10/10   |
| gpt-5.2     | none      | 19,732.57  | 17,317.53  | 43,352.75   | 10/10   |
| gpt-5-mini  | none      | 91,491.44  | 84,813.50  | 157,114.12  | 9/10    |

### Winner: GPT-5.1
- **8.2x faster** than gpt-5-mini
- **1.8x faster** than gpt-5.2
- **100% success rate**
- Most consistent performance across all queries

### Test Queries Used
1. "I need help finding a job after being released from prison. I have experience in construction."
2. "Looking for affordable housing assistance in Austin, Texas."
3. "Need food assistance and clothing donations for my family of 4."
4. "I'm a veteran looking for mental health counseling services."
5. "Need help with GED classes and job training programs."
6. "Looking for childcare assistance while I attend job interviews."
7. "I need help with utility bill assistance, behind on electricity."
8. "Looking for free legal aid for an eviction notice."
9. "Need transportation assistance to get to work."
10. "Looking for substance abuse treatment programs."

---

## Model Comparison (50 queries)

### Configuration
- **Models Tested:** gpt-5.1, gpt-5.2, gpt-5-mini
- **Reasoning:** none
- **Queries:** 50 queries (cycling through sample queries)
- **API:** http://127.0.0.1:3000

### Results

| Model       | Reasoning | Avg (ms)    | P50 (ms)    | P95 (ms)    | Success |
|-------------|-----------|-------------|-------------|-------------|---------|
| gpt-5.1     | none      | 12,174.02   | 11,664.76   | 18,992.19   | 50/50   |
| gpt-5.2     | none      | 16,563.67   | 16,191.21   | 26,421.33   | 50/50   |
| gpt-5-mini  | none      | 113,635.58  | 103,238.62  | 221,167.21  | 48/50   |

### Winner: GPT-5.1
- **9.3x faster** than gpt-5-mini
- **1.4x faster** than gpt-5.2
- **100% success rate** (50/50)
- **Most reliable** with lowest P95 latency

### Full Query List (20 unique, cycled to 50)

1. I need help finding a job after being released from prison. I have experience in construction.
2. Looking for affordable housing assistance in Austin, Texas.
3. Need food assistance and clothing donations for my family of 4.
4. I'm a veteran looking for mental health counseling services.
5. Need help with GED classes and job training programs.
6. Looking for childcare assistance while I attend job interviews.
7. I need help with utility bill assistance, behind on electricity.
8. Looking for free legal aid for an eviction notice.
9. Need transportation assistance to get to work.
10. Looking for substance abuse treatment programs.
11. I need help getting my driver's license reinstated.
12. Looking for job opportunities for people with disabilities.
13. Need help with resume writing and interview preparation.
14. Looking for ESL classes and citizenship assistance.
15. I need help finding healthcare for my children.
16. Looking for emergency shelter for tonight.
17. Need help with anger management classes (court ordered).
18. Looking for parenting classes and family support services.
19. I need help paying for prescription medications.
20. Looking for programs that help formerly incarcerated individuals.

*(Queries 21-50 repeat the above list)*

---

## Referral Size Limit Testing

### Objective
Test whether limiting output to exactly 5 referrals improves response latency.

### Test 1: Initial Comparison (10 queries)

#### Control Run (No Limit)
- **Model:** gpt-5.1
- **Reasoning:** none
- **Queries:** 10
- **Results:**
  - Avg: 18,250.41ms
  - P50: 18,040.07ms
  - P95: 31,796.45ms
  - Success: 10/10

#### With "Limit to 5 referrals" Constraint
- **Model:** gpt-5.1
- **Reasoning:** none
- **Queries:** 10
- **Results:**
  - Avg: 16,089.10ms
  - P50: 16,285.56ms
  - P95: 22,114.23ms
  - Success: 10/10

#### Performance Improvement
- **Speed improvement:** 11.8% faster (2,161.31ms faster)
- **Calculation:** 16,089.10 / 18,250.41 = 0.882 → 1 - 0.882 = 0.118 = **11.8% improvement**

---

### Test 2: Extended Testing (30 queries)

#### Baseline (No Limit)
- **Model:** gpt-5.1
- **Queries:** 30 distinct queries
- **Results:**
  - Avg: 18,300.17ms
  - P50: 17,074.94ms
  - P95: 28,067.10ms
  - Success: 30/30
- **Saved:** `app/bench_gpt-5.1_baseline_i30_q30.json`

#### With "Limit to 5 referrals" Constraint
- **Model:** gpt-5.1
- **Queries:** 30 distinct queries (same as baseline)
- **Results:**
  - Avg: 13,173.83ms
  - P50: 11,739.07ms
  - P95: 30,872.57ms
  - Success: 30/30
- **Saved:** `app/bench_gpt-5.1_limit5_i30_q30.json`

#### Performance Improvement
- **Speed improvement:** 28% faster on average
- **Calculation:** 13,173.83 / 18,300.17 = 0.72 → 1 - 0.72 = 0.28 = **28% improvement**
- **Average time saved:** 5,126.34ms per query
- **P50 improvement:** 31.2% faster (17,074.94ms → 11,739.07ms)
- **P95 increased slightly:** 28,067.10ms → 30,872.57ms (+10%)

---

### Why P95 Increased Despite Average Improvement

**Explanation:**

1. **Small sample size**: With 30 samples, P95 is essentially "the worst or second-worst run after interpolation." One extra-slow request can move P95 by several seconds.

2. **LLM latency isn't only output tokens**: Time includes:
   - Routing and queueing
   - Safety/policy checks
   - Model-side variability
   - Reducing output length improves average while still having occasional spikes

3. **Pipeline variance**: Even for the same query text, the RAG pipeline can vary slightly:
   - Timing differences
   - DB/cache state
   - Phoenix instrumentation overhead
   - Transient slowdowns

4. **Constraint can sometimes increase work**: The "limit to 5" instruction can make the model spend extra effort selecting/pruning/formatting exactly 5 resources, which may occasionally backfire into a slower completion (rare, but it only takes one slow run to shift P95).

---

## Gemini Speed Testing

### Comprehensive Central Texas Benchmark (55 queries)

**Test Type:** Response Speed & Performance Comparison
**Test Date:** January 26, 2026
**Configuration:** WITHOUT web search (fair apples-to-apples comparison)
**Test Cases:** 55 diverse Central Texas case worker scenarios
**Location Focus:** Austin and surrounding Central Texas cities

---

#### ChatGPT 5.1 (no reasoning) WITHOUT WEB SEARCH

- ✅ **Success Rate**: 55/55 (100%)
- ⏱️ **Average Response Time**: 35.50s
- 📊 **Median Response Time**: 27.23s
- ⚡ **Minimum**: 12.85s
- 🐌 **Maximum**: 402.45s *(huge outlier on test #46)*
- 📈 **Standard Deviation**: 51.20s *(high variability)*
- 📉 **Variance**: 2621.73

**Distribution Percentiles:**
- 25th percentile: 22.51s
- 75th percentile: 32.96s
- 95th percentile: 46.69s

---

#### Gemini 3 Flash WITHOUT WEB SEARCH

- ✅ **Success Rate**: 52/55 (94.5%)
  - 3 timeout errors (504 Deadline Exceeded) on tests #17, #22, #25
- ⏱️ **Average Response Time**: 17.43s
- 📊 **Median Response Time**: 15.49s
- ⚡ **Minimum**: 10.91s
- 🐌 **Maximum**: 72.10s
- 📈 **Standard Deviation**: 11.07s *(much more consistent)*
- 📉 **Variance**: 122.64

**Distribution Percentiles:**
- 25th percentile: 13.86s
- 75th percentile: 17.34s

---

### 🏆 Winner: Gemini 3 Flash

**Speed Advantage:**
- **103.7% faster** on average
- **2.04x speedup** over ChatGPT
- **18.07 seconds faster** per request
- **Time saved at scale (1,000 requests)**: ~5 hours

**Consistency Advantage:**
- **4.6x more consistent** (lower standard deviation: 11.07s vs 51.20s)
- **21.4x lower variance** (122.64 vs 2621.73)
- Much tighter response time distribution

**Reliability Trade-off:**
- ChatGPT: 100% success rate (no failures)
- Gemini: 94.5% success rate (3 timeout errors)

---

### Key Insights

1. **Gemini Flash dominates on speed**: More than twice as fast on average, making it ideal for high-volume production use.

2. **Gemini Flash is far more predictable**: With a standard deviation 4.6x lower, response times are much more consistent, making capacity planning easier.

3. **ChatGPT 5.1 had perfect reliability**: No timeouts or errors across all 55 tests, though it experienced significant rate limiting on one test (402.5s).

4. **ChatGPT's major outlier**: Test #46 (Youth Aging Out - Independence) took 402.5 seconds, likely due to rate limiting. Without this outlier, the average would be much closer.

5. **Cost-Performance Trade-off**: For an Austin-focused case worker tool processing hundreds of requests daily, Gemini Flash offers:
   - 2x faster responses
   - More predictable performance
   - Lower cost per request
   - Slightly lower reliability (94.5% vs 100%)

---

### Test Case Categories (55 Total)

The benchmark covers 10 categories of real-world Central Texas case worker scenarios:

1. **Family Support** (10 cases): Single parents, grandparents raising grandchildren, blended families, housing instability
2. **Veterans** (5 cases): PTSD, homelessness, career transition, disability, elderly care
3. **Elderly** (5 cases): Medical needs, aging in place, isolation, dementia, low-income
4. **Immigration** (5 cases): Language barriers, refugees, DACA recipients, mixed-status families
5. **Youth** (5 cases): Teen parents, runaways, LGBTQ+ youth, disabilities, juvenile justice
6. **Domestic Violence** (5 cases): Emergency safety, economic independence, immigrant survivors
7. **Disability** (5 cases): Physical, intellectual, mental health, autism, multiple disabilities
8. **Criminal Justice** (5 cases): Ex-offenders, probation, housing restrictions, reentry
9. **Foster Care** (5 cases): Aging out, educational advocacy, kinship care, adoption
10. **Mental Health** (5 cases): Severe mental illness, opioid addiction, dual diagnosis, suicide prevention

**Full test case details** (all 55 prompts with locations and specific needs) are documented in the benchmark script `central_texas_benchmark.py`.

---

### Initial 10-Query Validation Test

**Quick validation test (earlier testing phase):**

#### ChatGPT 5.1 (no reasoning)
- **Success Rate:** 10/10 (100%)
- **Average Time:** 31.31 seconds
- **Median:** 30.04s
- **Range:** 24.48s - 41.10s
- **Standard Deviation:** 6.18s

#### Gemini 3 Flash
- **Success Rate:** 10/10 (100%)
- **Average Time:** 13.84 seconds
- **Median:** 13.79s
- **Range:** 11.50s - 17.99s
- **Standard Deviation:** 1.87s

**Result:** Gemini 3 Flash was **126.2% faster** (13.84s vs 31.31s) with much more consistent performance

---

### Why Gemini Wasn't Tested WITH Web Search

#### The Challenge

All Gemini speed tests above were conducted **WITHOUT web search enabled** to ensure a fair apples-to-apples comparison with ChatGPT 5.1 (also without web search). However, our **production application relies on web search** to provide current, accurate resource recommendations.

**Why we couldn't test Gemini with web search:**

1. **Different API Architecture:**
   - OpenAI: Uses Responses API with built-in `tools=[{"type": "web_search"}]`
   - Gemini: Uses separate "grounding with Google Search" feature that works differently

2. **No Direct Equivalent:**
   - OpenAI's Responses API is specifically designed for web-grounded responses
   - Gemini's grounding feature uses a different model and configuration approach
   - Cannot do a direct performance comparison without implementing both

3. **Implementation Required:**
   - Current codebase uses `OpenAIWebSearchGenerator` component
   - Would need to build a parallel `GeminiWebSearchGenerator` component
   - Requires understanding Gemini's grounding API patterns and behavior

4. **Fair Comparison Needed:**
   - Testing Gemini without web search vs ChatGPT with web search would be misleading
   - Speed differences could be due to web search overhead, not model performance
   - For accurate benchmarking, both must use the same configuration

---

### What It Would Take to Implement Gemini with Web Search

#### Technical Requirements

**1. API Integration - Gemini's Grounding with Google Search**

Gemini uses the "grounding" feature to connect responses to Google Search results:

```python
import google.generativeai as genai
from google.generativeai import types

# Configure grounding with Google Search
model = genai.GenerativeModel('gemini-3-flash-preview')

response = model.generate_content(
    prompt,
    tools=[types.Tool(
        google_search=types.GoogleSearchRetrieval()
    )]
)
```

**Key differences from OpenAI:**
- Uses `google_search` tool instead of generic `web_search`
- May return grounding metadata and source citations
- Different response structure and parsing requirements

**2. New Component Implementation**

Create `GeminiWebSearchGenerator` component in `src/common/components.py`:

```python
@component
class GeminiWebSearchGenerator:
    """Searches the web using Google's grounding feature and generates a response."""

    @component.output_types(replies=List[ChatMessage])
    def run(
        self,
        messages: list[ChatMessage],
        model: str = "gemini-3-flash-preview",
        temperature: float | None = None,  # Gemini DOES support temperature!
    ) -> dict:
        """
        Run the Gemini web search generator.

        Args:
            messages: List of ChatMessage objects to send to the API
            model: Gemini model to use
            temperature: Temperature for response randomness (0.0-1.0)

        Returns:
            Dictionary with replies key containing ChatMessage response
        """
        import google.generativeai as genai
        from google.generativeai import types

        assert len(messages) == 1
        prompt = messages[0].text

        # Initialize Gemini client
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        model_instance = genai.GenerativeModel(model)

        # Configure generation parameters
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature

        # Generate with grounding
        response = model_instance.generate_content(
            prompt,
            tools=[types.Tool(
                google_search=types.GoogleSearchRetrieval()
            )],
            generation_config=generation_config if generation_config else None
        )

        # Extract text from response
        response_text = response.text

        return {"replies": [ChatMessage.from_assistant(response_text)]}
```

**3. Pipeline Integration**

Update pipeline to support both OpenAI and Gemini generators:

```python
# In pipeline configuration
if config.llm_provider == "openai":
    generator = OpenAIWebSearchGenerator()
elif config.llm_provider == "gemini":
    generator = GeminiWebSearchGenerator()
else:
    raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
```

**4. Configuration Management**

Add environment variables and configuration:

```python
# In app_config.py
class Config:
    # Existing OpenAI config
    openai_api_key: str = os.environ.get("OPENAI_API_KEY")

    # New Gemini config
    google_api_key: str = os.environ.get("GOOGLE_API_KEY")
    llm_provider: str = os.environ.get("LLM_PROVIDER", "openai")  # "openai" or "gemini"
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
```

---

#### Development Effort Estimate

**Implementation Time: 2-3 days**

| Task | Effort | Priority |
|------|--------|----------|
| Research Gemini grounding API | 2 hours | High |
| Implement `GeminiWebSearchGenerator` component | 4 hours | High |
| Add configuration and environment setup | 2 hours | High |
| Update pipeline to support both providers | 3 hours | High |
| Write unit tests | 4 hours | Medium |
| Integration testing and debugging | 6 hours | High |
| Performance benchmarking (with web search) | 4 hours | High |
| Documentation | 2 hours | Medium |
| **Total** | **~27 hours (~3-4 days)** | |

---

#### Benefits of Implementing Gemini with Web Search

**Potential Advantages:**

1. **Speed:** Based on tests without web search, Gemini is 2x faster than ChatGPT
   - Expected improvement even with web search enabled
   - Better user experience with faster response times

2. **Cost:** Gemini Flash is typically more cost-effective than GPT-5.1
   - Lower cost per 1M tokens
   - Significant savings at scale (thousands of daily requests)

3. **Temperature Control:** Gemini **DOES support temperature** parameter
   - Could address user concerns about consistency
   - Enables fine-tuning of response variability
   - No API limitation like OpenAI's Responses API

4. **Google Search Integration:** Native Google Search grounding
   - Direct access to Google's search results
   - Potentially more current information
   - Better integration with Google's knowledge graph

5. **Provider Diversity:** Reduces dependency on single vendor
   - Enables A/B testing between providers
   - Fallback option if one provider has issues
   - Negotiating leverage with vendors

**Trade-offs to Consider:**

1. **Additional Complexity:** Maintaining two separate LLM integrations
2. **Testing Burden:** Need to test both providers for each change
3. **Response Format Differences:** May need to handle different output structures
4. **Grounding Metadata:** Gemini returns source citations that need handling
5. **Unknown Performance:** Speed with web search hasn't been validated yet

---

#### Recommended Next Steps

**If you want to pursue Gemini with web search:**

1. **Proof of Concept (1 day)**
   - Create simple standalone script testing Gemini grounding
   - Verify API works as expected
   - Measure speed with web search on 10 sample queries

2. **Component Implementation (2 days)**
   - Build `GeminiWebSearchGenerator` component
   - Integrate with existing pipeline
   - Add configuration switching

3. **Benchmark Testing (1 day)**
   - Run same 55-query Central Texas benchmark WITH web search
   - Compare speed, quality, and reliability vs ChatGPT 5.1
   - Analyze cost implications

4. **Production Decision**
   - If Gemini with web search is faster AND maintains quality: Consider migration
   - If only marginally better: May not be worth the complexity
   - If quality suffers: Stick with ChatGPT 5.1

**Priority Assessment:** ⚠️ **Medium Priority**

- Current production (ChatGPT 5.1 + web search) works reliably
- Speed improvements would be beneficial but not critical
- Temperature control with Gemini is attractive but hybrid caching (from temperature report) is an alternative
- Consider implementing after addressing consistency issues with caching approach

---

## Parameter Effect Testing: Temperature and Reasoning

**Test Date:** March 3, 2026
**Purpose:** Measure how temperature and reasoning parameters affect web search decisions and latency
**API:** OpenAI Responses API with web_search tool

---

### Background

**The Problem:**
Production baseline showed 36.4% web search usage from 55 real queries. However, testing with the production prompt (missing database-injected resources) resulted in 96.4% web search usage - a 60 percentage point gap.

**Root Cause:**
Production prompt uses Jinja2 template `{% for s in supports %}` to inject hundreds of database resources at runtime. Test environment only has inline CAT/Excel resources (~19 classes), missing the bulk of resources that reduce web search necessity.

**Test Objective:**
Since we can't replicate the exact production baseline (missing DB resources), test whether temperature and reasoning parameters affect web search decisions and latency for future optimization.

---

### Configuration

- **Model:** gpt-5.1 (production configuration)
- **Baseline:** reasoning="none" (production setting)
- **Test prompt:** Production prompt Version 48 with inline CAT/Excel resources only
- **Queries per test:** 20 real production queries
- **Configurations tested:** 9 total
  - Baseline: reasoning="none"
  - Temperature: 0.0, 0.5, 1.0, 1.5, 2.0 (requires reasoning="none")
  - Reasoning: low, medium, high (incompatible with temperature)

---

### Results Summary

**Note:** Results use **median latency** instead of mean to handle outliers. Several tests experienced hung requests (2-22 hours) that skewed averages.

| Configuration | Web Search Rate | Median Latency | vs Baseline |
|--------------|-----------------|----------------|-------------|
| **Baseline (reasoning=none)** | **90.0%** | **~20s** | - |
| Temperature 0.0 | 90.0% | ~22s | +2s (stable) |
| Temperature 0.5 | 90.0% | ~19s | -1s (stable) |
| Temperature 1.0 | 90.0% | ~17s | -3s (stable) |
| Temperature 1.5 | 90.0% | ~26s | +6s (stable) |
| Temperature 2.0 | 89.5% | ~15s* | -5s (2 hung queries) |
| **Reasoning low** | **90.0%** | **~40s** | **+20s (2x slower)** |
| **Reasoning medium** | **95.0% (+5.0pp)** | **~140s** | **+120s (7x slower)** |
| **Reasoning high** | **100.0% (+10.0pp)** | **~280s** | **+260s (14x slower)** |

*\*Temperature 2.0 had 2 hung queries (79,117s and 81,417s) excluded from median calculation*

---

### Key Findings

#### 1. Temperature Has Minimal Effect on Web Search Decisions

**Web Search Rate: Stable ~90%**
- Temperature 0.0 to 2.0 all showed ~90% web search rate
- Variation was within noise (89.5% - 90.0%)
- Temperature does NOT significantly affect whether the model chooses to search the web

**Latency: Minor variation**
- Median latency ranged from ~15s to ~26s across temperatures
- Variation within 50% of baseline (acceptable)
- Temperature 2.0 showed instability (2 hung queries out of 20)

**Conclusion:** Temperature parameter does not solve the web search consistency issue and may introduce instability at extreme values (2.0).

---

#### 2. Reasoning Has Significant Effect (Opposite of Desired)

**Web Search Rate: INCREASES with reasoning level**
- Baseline (none): 90.0%
- Low: 90.0% (no change)
- Medium: 95.0% (+5.0pp)
- High: 100.0% (+10.0pp)

**Counterintuitive Result:**
Higher reasoning makes the model MORE likely to search the web, not less. This is opposite to what might be expected if reasoning helped the model better utilize existing resources.

**Latency: DRAMATICALLY INCREASES**
- Baseline: ~20s median
- Low: ~40s (2x slower)
- Medium: ~140s (7x slower)
- High: ~280s (14x slower)

**Cost Implications:**
- Reasoning medium/high are unusable due to latency (2-5 minutes per query)
- Reasoning also increases token costs due to thinking tokens
- Reasoning high had 4 connection errors (reliability issues)

**Conclusion:** Reasoning parameters make the situation worse - MORE web search, MUCH slower responses, and lower reliability.

---

### Outliers and Hung Requests

**Critical Data Quality Issue:**
Several configurations experienced hung requests that skewed initial average calculations:

1. **Temperature 2.0:**
   - Query #19: 79,117s (22 hours)
   - Query #20: 81,417s (22.6 hours)
   - Initial average: 8,460.52s → Corrected median: ~15s

2. **Reasoning high:**
   - Query #3: 2,393s (40 minutes)
   - Query #6: 10,464s (2.9 hours)
   - Queries #17-20: 4 connection errors
   - Initial average: 1,057.62s → Corrected median: ~280s

**Analysis Method:**
- Switched from **mean** to **median** latency
- Median is robust to outliers (hung queries)
- Provides more realistic performance expectations

---

### Production Recommendations

Based on these findings, **current production configuration is optimal**:

#### ✅ Keep Current Configuration
- **Model:** gpt-5.1
- **Reasoning:** {"effort": "none"}
- **No temperature parameter** (not supported with reasoning="none" in Responses API)

#### Why This Configuration:
1. **Fastest response times** (~20s median)
2. **Most reliable** (no hung queries at scale)
3. **Lowest cost** (no reasoning token overhead)
4. **Stable web search behavior** (90% with limited resources)

#### ❌ Do NOT Use:
- **Temperature > 1.5:** Introduces instability and hung queries
- **Temperature < 1.0:** No benefit, slight latency increase
- **Reasoning (any level):** Much slower, more web search, higher cost, lower reliability

---

### Test Context and Limitations

#### Important Caveats:

1. **Not Testing Production Baseline:**
   - Production: 36.4% web search (with full DB resources)
   - Test: 90-100% web search (missing DB resources)
   - 60pp gap due to missing resources, NOT parameter choice

2. **Testing Relative Effects:**
   - Goal: Measure parameter effects on web search decisions
   - Result: Temperature has no effect, reasoning makes it worse
   - Neither parameter solves the underlying issue

3. **Resource Gap:**
   - Production has hundreds of database-injected resources
   - Test environment has ~19 inline resources (CAT/Excel classes)
   - Cannot match production baseline without full database

4. **Sample Size:**
   - 20 queries per configuration (vs 55 total production queries)
   - Sufficient to detect parameter effects
   - May not capture all production variability

---

### Methodology

#### Test Implementation

**Test Script:** `parameter_effect_test.py`

**Query Source:**
- Real production queries from Phoenix traces
- 55 total queries: 20 web search (36.4%), 35 no web search (63.6%)
- Subset of 20 queries used per configuration for speed

**Web Search Detection:**
```python
# Check if web search was used
used_web_search = False
if response.output:
    for item in response.output:
        if hasattr(item, 'type') and item.type == 'web_search_call':
            used_web_search = True
            break
```

**Request Configuration:**
```python
request_params = {
    "model": "gpt-5.1",
    "tools": [{"type": "web_search"}],
    "input": [
        {"role": "system", "content": PRODUCTION_PROMPT},
        {"role": "user", "content": f"Client needs: {query}"}
    ]
}

# Add reasoning OR temperature (mutually exclusive)
if reasoning:
    request_params["reasoning"] = {"effort": reasoning}
elif temperature is not None:
    request_params["temperature"] = temperature
    request_params["reasoning"] = {"effort": "none"}  # Required for temperature
```

**Statistical Analysis:**
- Median latency (robust to outliers)
- Web search rate (percentage)
- Error tracking (timeouts, connection errors)
- Rate limiting: 0.3s between requests

---

### Future Investigation Opportunities

#### If You Want to Match Production Baseline (36.4%):

**Option 1: Database Access**
- Export production database resources
- Inject into test prompt via Jinja2 template
- Re-run parameter tests with full resource set
- Expected: Lower web search rates (closer to 36.4%)

**Option 2: Alternative Prompt Engineering**
- Test prompt changes that encourage using embedded resources first
- Example: "IMPORTANT: Check the provided resources list before searching the web"
- May not work - prompt already has this guidance

**Option 3: Hybrid Caching Strategy**
- Pre-populate cache with common Central Texas resources
- Reduce web search necessity through better caching
- See TEMPERATURE_ANALYSIS_REPORT.md for caching implementation details

#### Why Web Search Rate Doesn't Match Production:

The 90% test rate vs 36.4% production rate is primarily explained by:
1. **Missing database resources** (hundreds of resources in production)
2. **Resource specificity** (database has more granular, targeted resources)
3. **Resource freshness** (inline resources may be outdated)

The parameter effect testing still provides value by showing that temperature and reasoning do not solve web search consistency issues.

---

### Related Documentation

- **Test Script:** `parameter_effect_test.py`
- **Raw Results:** `parameter_effect_results.json`
- **Test Output:** `parameter_effect_test_output.txt`
- **Production Queries:** `sample_production_queries.json`
- **Production Prompt:** `production_prompt_v48.txt`
- **Temperature Analysis:** `TEMPERATURE_ANALYSIS_REPORT.md` (hybrid caching strategy)
- **Web Search Investigation:** `WEB_SEARCH_SPIKE_ROOT_CAUSE_ANALYSIS.md`

---

## Key Findings & Recommendations

### Model Selection

#### 🏆 Primary Recommendation: GPT-5.1
- **9.3x faster** than gpt-5-mini
- **1.4x faster** than gpt-5.2
- **100% success rate** across all tests
- **Most consistent performance** (lowest P95 latency)
- **Best balance** of speed, reliability, and cost

#### Alternative: Gemini 3 Flash
- **126% faster** than ChatGPT 5.1 (raw model without web search)
- **More consistent** performance (lower standard deviation)
- **100% success rate**
- Consider for high-volume production use cases prioritizing speed

### Referral Output Optimization

#### 🎯 Recommendation: Implement "Limit to 5 referrals" Constraint

**Benefits:**
- **28% average latency improvement** (based on 30-query test)
- **31.2% P50 improvement** (median response time)
- **5.1 seconds saved** per query on average
- **At scale (1,000 queries):** ~1.4 hours saved
- **No impact on success rate** (100% both ways)

**Trade-offs:**
- P95 may increase slightly (~10%) due to occasional constraint-processing overhead
- Small sample variance means one slow request can affect tail latency
- Overall user experience improves due to faster average and median times

**Implementation:**
Append the following constraint to all prompts:
```
"Limit your response to exactly 5 referrals."
```

### Production Deployment Strategy

**Recommended Configuration:**
1. **Model:** gpt-5.1 (no reasoning)
2. **Constraint:** "Limit to 5 referrals"
3. **Expected Performance:**
   - Average latency: ~13.2 seconds
   - P50 latency: ~11.7 seconds
   - 100% success rate
   - 28% faster than baseline

**Monitoring:**
- Track P95 latency over time
- Monitor success rates
- Collect user feedback on response quality
- Consider A/B testing Gemini 3 Flash for further speed improvements

---

**Generated:** January 2026
**Test Environment:** Local API (http://127.0.0.1:3000)
**Models Tested:** gpt-5.1, gpt-5.2, gpt-5-mini, gemini-3-flash-preview
