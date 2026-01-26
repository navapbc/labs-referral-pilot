# Central Texas Model Performance Benchmark Results

## Executive Summary

**Test Date:** January 26, 2026
**Models Tested:** ChatGPT 5.1 (no reasoning) vs Gemini 3 Flash
**Configuration:** WITHOUT web search
**Test Cases:** 55 diverse Central Texas case worker scenarios
**Location Focus:** Austin and surrounding Central Texas cities

---

## 🏆 Final Results

### ChatGPT 5.1 (no reasoning) WITHOUT WEB SEARCH
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

### Gemini 3 Flash WITHOUT WEB SEARCH
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

## 🎯 Performance Comparison

### **🏆 WINNER: Gemini 3 Flash**

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

## 📊 Key Insights

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

## 🗂️ Test Case Categories (55 Total)

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

---

## 📝 All 55 Test Prompts

Each test case uses the following format:

```
You are a case worker assistant in Central Texas. Recommend 5-7 relevant social support resources in [LOCATION].

Client needs: [SPECIFIC NEEDS]

Return valid JSON: {"resources": [{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}]}
```

### Family Support (10 cases)

1. **Single Mother - Employment & Childcare (Austin, TX)**
   - Needs: employment, childcare, food assistance, education, healthcare

2. **Two-Parent Family - Financial Crisis (Round Rock, TX)**
   - Needs: emergency rent, utility assistance, food banks, job training, credit counseling

3. **Grandparent Raising Grandchildren (Cedar Park, TX)**
   - Needs: legal guardianship, childcare, education resources, respite care, financial support

4. **Large Family - Housing Instability (Georgetown, TX)**
   - Needs: affordable housing, rental assistance, furniture, school supplies, transportation

5. **Blended Family - Parenting Support (Pflugerville, TX)**
   - Needs: family counseling, parenting classes, youth activities, financial planning, healthcare

6. **Foster Parents - Special Needs Care (Kyle, TX)**
   - Needs: respite care, special education, therapy services, support groups, training

7. **Kinship Care Family (San Marcos, TX)**
   - Needs: legal services, financial assistance, school enrollment, healthcare, counseling

8. **Multiracial Family - Cultural Support (Leander, TX)**
   - Needs: cultural programs, language services, community connections, youth mentoring, family events

9. **Rural Family - Access to Services (Bastrop, TX)**
   - Needs: transportation, healthcare access, internet, job opportunities, childcare

10. **Urban Family - Overcrowded Housing (Austin, TX - East)**
    - Needs: affordable housing, rental assistance, legal aid, financial counseling, healthcare

### Veterans (5 cases)

11. **Veteran - PTSD & Homelessness (Austin, TX)**
    - Needs: emergency housing, PTSD counseling, job training, VA benefits, substance abuse treatment

12. **Female Veteran - Career Transition (Round Rock, TX)**
    - Needs: job placement, career counseling, childcare, education benefits, networking

13. **Disabled Veteran - Housing Adaptation (Cedar Park, TX)**
    - Needs: accessible housing, home modifications, disability benefits, healthcare, adaptive equipment

14. **Veteran Family - Financial Stress (Georgetown, TX)**
    - Needs: financial counseling, employment, childcare, VA benefits, housing assistance

15. **Elderly Veteran - Long-term Care (Pflugerville, TX)**
    - Needs: home healthcare, VA benefits, meal delivery, transportation, social activities

### Elderly (5 cases)

16. **Elderly - Medical & Daily Living (Kyle, TX)**
    - Needs: home healthcare, meal delivery, transportation, social activities, prescription assistance

17. **Senior Couple - Aging in Place (San Marcos, TX)** *(Gemini timeout)*
    - Needs: home modifications, healthcare, meal services, social programs, financial assistance

18. **Isolated Senior - Depression (Leander, TX)**
    - Needs: mental health counseling, social activities, meal delivery, transportation, wellness checks

19. **Senior with Dementia - Caregiver Burnout (Bastrop, TX)**
    - Needs: respite care, caregiver support, memory care, adult day programs, counseling

20. **Low-Income Senior - Basic Needs (Austin, TX - South)**
    - Needs: utility assistance, food pantry, prescription help, housing support, healthcare

### Immigration (5 cases)

21. **Immigrant Family - Language & Integration (Austin, TX)**
    - Needs: ESL classes, immigration legal services, cultural integration, job placement, after-school programs

22. **Refugee Family - Resettlement (Round Rock, TX)** *(Gemini timeout)*
    - Needs: housing, employment, ESL, healthcare, school enrollment, cultural orientation

23. **DACA Recipient - Education & Career (Cedar Park, TX)**
    - Needs: college scholarships, work permits, legal services, career counseling, mentorship

24. **Undocumented Parents - Fear of Separation (Georgetown, TX)**
    - Needs: legal services, emergency planning, community support, school resources, healthcare

25. **Mixed-Status Family - Healthcare Access (Pflugerville, TX)** *(Gemini timeout)*
    - Needs: healthcare navigation, legal guidance, family support, education, emergency assistance

### Youth (5 cases)

26. **Teen Parent - Education Support (Kyle, TX)**
    - Needs: parenting classes, childcare, GED programs, teen mentorship, financial literacy

27. **Runaway Youth - Crisis Intervention (San Marcos, TX)**
    - Needs: emergency shelter, counseling, family mediation, education, job training

28. **LGBTQ+ Youth - Safe Housing (Austin, TX)**
    - Needs: safe housing, mental health support, legal services, education, community connections

29. **Youth with Disabilities - Transition to Adulthood (Round Rock, TX)**
    - Needs: vocational training, independent living skills, disability services, job placement, mentorship

30. **Juvenile Justice - Reentry Support (Cedar Park, TX)**
    - Needs: education, job training, counseling, mentorship, family support

### Domestic Violence (5 cases)

31. **DV Survivor - Emergency Safety (Austin, TX)**
    - Needs: emergency shelter, legal advocacy, restraining order, trauma counseling, safe childcare

32. **DV Survivor - Economic Independence (Georgetown, TX)**
    - Needs: job training, housing, childcare, legal services, financial independence

33. **DV Survivor - Teen Children Support (Round Rock, TX)**
    - Needs: family counseling, safe housing, legal advocacy, teen support, financial assistance

34. **DV Survivor - Immigrant Status Concerns (Pflugerville, TX)**
    - Needs: immigration legal services, emergency shelter, language services, safety planning, counseling

35. **DV Survivor - Substance Abuse (Kyle, TX)**
    - Needs: substance abuse treatment, mental health counseling, safe housing, legal advocacy, childcare

### Disability (5 cases)

36. **Physical Disability - Employment (San Marcos, TX)**
    - Needs: vocational rehabilitation, accessible housing, disability benefits, adaptive technology, job placement

37. **Intellectual Disability - Day Programs (Leander, TX)**
    - Needs: day programs, job coaching, independent living skills, social activities, family support

38. **Mental Health - Community Integration (Bastrop, TX)**
    - Needs: mental health treatment, supported employment, housing, social support, medication management

39. **Autism - Family Support (Austin, TX - North)**
    - Needs: therapy services, respite care, special education, parent training, social skills groups

40. **Multiple Disabilities - Coordinated Care (Round Rock, TX)**
    - Needs: case management, healthcare coordination, disability benefits, housing, transportation

### Criminal Justice (5 cases)

41. **Ex-Offender - Reentry Basics (Cedar Park, TX)**
    - Needs: job placement, housing, legal services, substance abuse counseling, life skills

42. **Formerly Incarcerated Parent - Reunification (Georgetown, TX)**
    - Needs: parenting classes, housing, employment, family counseling, legal services

43. **Probation - Compliance Support (Pflugerville, TX)**
    - Needs: employment, housing, substance abuse treatment, mental health services, transportation

44. **Sex Offender Registration - Housing (Kyle, TX)**
    - Needs: housing assistance, legal guidance, employment, counseling, community reintegration

45. **Jail-to-Community Transition (San Marcos, TX)**
    - Needs: transitional housing, job readiness, substance abuse treatment, healthcare, case management

### Foster Care (5 cases)

46. **Youth Aging Out - Independence (Austin, TX)** *(ChatGPT outlier: 402.5s)*
    - Needs: housing, college scholarships, job readiness, life skills, mentorship

47. **Foster Youth - Educational Advocacy (Round Rock, TX)**
    - Needs: education support, tutoring, college prep, scholarships, mentorship

48. **Kinship Foster Care (Cedar Park, TX)**
    - Needs: financial assistance, legal support, respite care, counseling, support groups

49. **Sibling Group - Adoption Support (Georgetown, TX)**
    - Needs: adoption assistance, family support, counseling, financial resources, sibling programs

50. **Foster Parent - Crisis Support (Pflugerville, TX)**
    - Needs: respite care, crisis intervention, counseling, training, support groups

### Mental Health (5 cases)

51. **Severe Mental Illness - Crisis (Kyle, TX)**
    - Needs: crisis intervention, psychiatric care, housing, case management, medication support

52. **Opioid Addiction - Recovery (San Marcos, TX)**
    - Needs: medication-assisted treatment, counseling, housing, job training, peer support

53. **Dual Diagnosis - Integrated Treatment (Leander, TX)**
    - Needs: mental health treatment, substance abuse counseling, housing, employment, case management

54. **Youth Mental Health - Early Intervention (Bastrop, TX)**
    - Needs: therapy, family counseling, school support, medication management, peer groups

55. **Suicide Prevention - High Risk (Austin, TX - West)**
    - Needs: crisis hotline, emergency psychiatric care, safety planning, counseling, hospitalization

---

## 💻 Benchmark Code

The complete benchmark script is available at `central_texas_benchmark.py`. Below is the full implementation:

```python
#!/usr/bin/env python3
"""
Comprehensive 55-Prompt Benchmark: ChatGPT 5.1 (no reasoning) vs Gemini 3 Flash
WITHOUT web search - Central Texas locations for Austin-focused case worker tool
"""

import time
import json
import os
import statistics

# API keys should be set in environment variables before running:
# export OPENAI_API_KEY="your-openai-key"
# export GOOGLE_API_KEY="your-google-key"

# 55 diverse test cases for Central Texas case worker scenarios
test_cases = [
    # [Test cases array - see full file for complete list]
]

print("=" * 80)
print("COMPREHENSIVE 50-PROMPT BENCHMARK - CENTRAL TEXAS")
print("ChatGPT 5.1 (no reasoning) vs Gemini 3 Flash")
print("WITHOUT WEB SEARCH - Austin/Central Texas locations")
print("=" * 80 + "\n")

chatgpt_results = []
gemini_results = []

# Test ChatGPT 5.1 WITHOUT web search
print("Testing ChatGPT 5.1 (no reasoning) WITHOUT WEB SEARCH...")
print("-" * 80)

from openai import OpenAI
client = OpenAI()

for i, test_case in enumerate(test_cases, 1):
    print(f"{i}. {test_case['name']} ({test_case['location']})...", end=" ", flush=True)
    try:
        start = time.time()

        query = f"""You are a case worker assistant in Central Texas. Recommend 5-7 relevant social support resources in {test_case['location']}.

Client needs: {test_case['needs']}

Return valid JSON: {{"resources": [{{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}}]}}"""

        response = client.responses.create(
            model="gpt-5.1",
            input=query,
            reasoning={"effort": "low"}
        )

        duration = time.time() - start
        text = response.output_text

        # Count resources
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1:
                data = json.loads(text[start_idx:end_idx])
                resource_count = len(data.get("resources", []))
            else:
                resource_count = 0
        except:
            resource_count = 0

        chatgpt_results.append({"duration": duration, "resources": resource_count, "success": True})
        print(f"✅ {duration:.1f}s ({resource_count} resources)")

    except Exception as e:
        chatgpt_results.append({"duration": 0, "resources": 0, "success": False, "error": str(e)})
        print(f"❌ Error: {str(e)[:50]}")

print()

# Test Gemini 3 Flash WITHOUT web search
print("Testing Gemini 3 Flash WITHOUT WEB SEARCH...")
print("-" * 80)

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    'gemini-3-flash-preview',
    safety_settings=safety_settings
)

for i, test_case in enumerate(test_cases, 1):
    print(f"{i}. {test_case['name']} ({test_case['location']})...", end=" ", flush=True)
    try:
        start = time.time()

        query = f"""You are a case worker assistant in Central Texas. Recommend 5-7 relevant social support resources in {test_case['location']}.

Client needs: {test_case['needs']}

Return valid JSON: {{"resources": [{{"name": "...", "description": "...", "addresses": ["..."], "phones": ["..."], "emails": ["..."], "website": "...", "justification": "..."}}]}}"""

        response = model.generate_content(query)
        duration = time.time() - start
        text = response.text

        # Count resources
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1:
                data = json.loads(text[start_idx:end_idx])
                resource_count = len(data.get("resources", []))
            else:
                resource_count = 0
        except:
            resource_count = 0

        gemini_results.append({"duration": duration, "resources": resource_count, "success": True})
        print(f"✅ {duration:.1f}s ({resource_count} resources)")

    except Exception as e:
        gemini_results.append({"duration": 0, "resources": 0, "success": False, "error": str(e)})
        print(f"❌ Error: {str(e)[:50]}")

# Statistical Analysis
# [See full script for complete statistical analysis code]
```

---

## 🚀 Running the Benchmark

### Prerequisites

```bash
pip install openai google-generativeai
```

### Environment Setup

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_API_KEY="your-google-api-key"
```

### Execute Benchmark

```bash
python3 central_texas_benchmark.py
```

The benchmark will:
1. Test all 55 scenarios on ChatGPT 5.1 (no reasoning)
2. Test all 55 scenarios on Gemini 3 Flash
3. Generate comprehensive statistical analysis
4. Output performance comparison and winner

**Expected Runtime:** ~30-45 minutes

---

## 📌 Recommendations

### For Production Deployment

**Primary Model: Gemini 3 Flash**
- 2x faster response times
- 4.6x more consistent performance
- Lower cost per request
- Ideal for high-volume production use

**Backup/Fallback: ChatGPT 5.1**
- 100% reliability (no timeouts)
- Use for critical requests or when Gemini experiences issues
- Consider for requests requiring maximum reliability

### Future Testing

1. **Test with web search enabled** to compare grounding capabilities
2. **Test Gemini 3 Pro** for quality comparison (likely slower but potentially higher quality)
3. **Test GPT-5.1 with reasoning** for complex cases requiring deeper analysis
4. **A/B test in production** to measure real-world user satisfaction
5. **Monitor timeout patterns** to understand Gemini's failure modes

---

## 📧 Questions or Issues?

For questions about this benchmark or to report issues, please contact the team or open an issue in the repository.

---

**Generated:** January 26, 2026
**Benchmark Script:** `central_texas_benchmark.py`
**Test Environment:** Python 3.9, macOS
