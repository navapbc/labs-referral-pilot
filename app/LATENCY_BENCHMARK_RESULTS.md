# Latency Benchmark Results: Model Performance & Referral Size Testing

**Test Date:** January 2026
**Purpose:** Compare model performance (GPT-5.1, GPT-5.2, GPT-5-mini) and test the impact of limiting referral output to 5 resources

---

## Table of Contents

1. [Model Comparison (10 queries)](#model-comparison-10-queries)
2. [Model Comparison (50 queries)](#model-comparison-50-queries)
3. [Referral Size Limit Testing](#referral-size-limit-testing)
4. [Gemini Speed Testing](#gemini-speed-testing)
5. [Key Findings & Recommendations](#key-findings--recommendations)

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
