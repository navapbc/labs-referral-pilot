#!/usr/bin/env python3
"""
Comprehensive 50-Prompt Benchmark: ChatGPT 5.1 (no reasoning) vs Gemini 3 Flash
WITHOUT web search - Central Texas locations for Austin-focused case worker tool
"""

import time
import json
import os
import statistics

# API keys should be set in environment variables before running:
# export OPENAI_API_KEY="your-openai-key"
# export GOOGLE_API_KEY="your-google-key"

# 50 diverse test cases for Central Texas case worker scenarios
test_cases = [
    # Family Support (10 cases)
    {"name": "Single Mother - Employment & Childcare", "location": "Austin, TX", "needs": "employment, childcare, food assistance, education, healthcare"},
    {"name": "Two-Parent Family - Financial Crisis", "location": "Round Rock, TX", "needs": "emergency rent, utility assistance, food banks, job training, credit counseling"},
    {"name": "Grandparent Raising Grandchildren", "location": "Cedar Park, TX", "needs": "legal guardianship, childcare, education resources, respite care, financial support"},
    {"name": "Large Family - Housing Instability", "location": "Georgetown, TX", "needs": "affordable housing, rental assistance, furniture, school supplies, transportation"},
    {"name": "Blended Family - Parenting Support", "location": "Pflugerville, TX", "needs": "family counseling, parenting classes, youth activities, financial planning, healthcare"},
    {"name": "Foster Parents - Special Needs Care", "location": "Kyle, TX", "needs": "respite care, special education, therapy services, support groups, training"},
    {"name": "Kinship Care Family", "location": "San Marcos, TX", "needs": "legal services, financial assistance, school enrollment, healthcare, counseling"},
    {"name": "Multiracial Family - Cultural Support", "location": "Leander, TX", "needs": "cultural programs, language services, community connections, youth mentoring, family events"},
    {"name": "Rural Family - Access to Services", "location": "Bastrop, TX", "needs": "transportation, healthcare access, internet, job opportunities, childcare"},
    {"name": "Urban Family - Overcrowded Housing", "location": "Austin, TX (East)", "needs": "affordable housing, rental assistance, legal aid, financial counseling, healthcare"},

    # Veterans (5 cases)
    {"name": "Veteran - PTSD & Homelessness", "location": "Austin, TX", "needs": "emergency housing, PTSD counseling, job training, VA benefits, substance abuse treatment"},
    {"name": "Female Veteran - Career Transition", "location": "Round Rock, TX", "needs": "job placement, career counseling, childcare, education benefits, networking"},
    {"name": "Disabled Veteran - Housing Adaptation", "location": "Cedar Park, TX", "needs": "accessible housing, home modifications, disability benefits, healthcare, adaptive equipment"},
    {"name": "Veteran Family - Financial Stress", "location": "Georgetown, TX", "needs": "financial counseling, employment, childcare, VA benefits, housing assistance"},
    {"name": "Elderly Veteran - Long-term Care", "location": "Pflugerville, TX", "needs": "home healthcare, VA benefits, meal delivery, transportation, social activities"},

    # Elderly (5 cases)
    {"name": "Elderly - Medical & Daily Living", "location": "Kyle, TX", "needs": "home healthcare, meal delivery, transportation, social activities, prescription assistance"},
    {"name": "Senior Couple - Aging in Place", "location": "San Marcos, TX", "needs": "home modifications, healthcare, meal services, social programs, financial assistance"},
    {"name": "Isolated Senior - Depression", "location": "Leander, TX", "needs": "mental health counseling, social activities, meal delivery, transportation, wellness checks"},
    {"name": "Senior with Dementia - Caregiver Burnout", "location": "Bastrop, TX", "needs": "respite care, caregiver support, memory care, adult day programs, counseling"},
    {"name": "Low-Income Senior - Basic Needs", "location": "Austin, TX (South)", "needs": "utility assistance, food pantry, prescription help, housing support, healthcare"},

    # Immigration (5 cases)
    {"name": "Immigrant Family - Language & Integration", "location": "Austin, TX", "needs": "ESL classes, immigration legal services, cultural integration, job placement, after-school programs"},
    {"name": "Refugee Family - Resettlement", "location": "Round Rock, TX", "needs": "housing, employment, ESL, healthcare, school enrollment, cultural orientation"},
    {"name": "DACA Recipient - Education & Career", "location": "Cedar Park, TX", "needs": "college scholarships, work permits, legal services, career counseling, mentorship"},
    {"name": "Undocumented Parents - Fear of Separation", "location": "Georgetown, TX", "needs": "legal services, emergency planning, community support, school resources, healthcare"},
    {"name": "Mixed-Status Family - Healthcare Access", "location": "Pflugerville, TX", "needs": "healthcare navigation, legal guidance, family support, education, emergency assistance"},

    # Youth (5 cases)
    {"name": "Teen Parent - Education Support", "location": "Kyle, TX", "needs": "parenting classes, childcare, GED programs, teen mentorship, financial literacy"},
    {"name": "Runaway Youth - Crisis Intervention", "location": "San Marcos, TX", "needs": "emergency shelter, counseling, family mediation, education, job training"},
    {"name": "LGBTQ+ Youth - Safe Housing", "location": "Austin, TX", "needs": "safe housing, mental health support, legal services, education, community connections"},
    {"name": "Youth with Disabilities - Transition to Adulthood", "location": "Round Rock, TX", "needs": "vocational training, independent living skills, disability services, job placement, mentorship"},
    {"name": "Juvenile Justice - Reentry Support", "location": "Cedar Park, TX", "needs": "education, job training, counseling, mentorship, family support"},

    # Domestic Violence (5 cases)
    {"name": "DV Survivor - Emergency Safety", "location": "Austin, TX", "needs": "emergency shelter, legal advocacy, restraining order, trauma counseling, safe childcare"},
    {"name": "DV Survivor - Economic Independence", "location": "Georgetown, TX", "needs": "job training, housing, childcare, legal services, financial independence"},
    {"name": "DV Survivor - Teen Children Support", "location": "Round Rock, TX", "needs": "family counseling, safe housing, legal advocacy, teen support, financial assistance"},
    {"name": "DV Survivor - Immigrant Status Concerns", "location": "Pflugerville, TX", "needs": "immigration legal services, emergency shelter, language services, safety planning, counseling"},
    {"name": "DV Survivor - Substance Abuse", "location": "Kyle, TX", "needs": "substance abuse treatment, mental health counseling, safe housing, legal advocacy, childcare"},

    # Disability (5 cases)
    {"name": "Physical Disability - Employment", "location": "San Marcos, TX", "needs": "vocational rehabilitation, accessible housing, disability benefits, adaptive technology, job placement"},
    {"name": "Intellectual Disability - Day Programs", "location": "Leander, TX", "needs": "day programs, job coaching, independent living skills, social activities, family support"},
    {"name": "Mental Health - Community Integration", "location": "Bastrop, TX", "needs": "mental health treatment, supported employment, housing, social support, medication management"},
    {"name": "Autism - Family Support", "location": "Austin, TX (North)", "needs": "therapy services, respite care, special education, parent training, social skills groups"},
    {"name": "Multiple Disabilities - Coordinated Care", "location": "Round Rock, TX", "needs": "case management, healthcare coordination, disability benefits, housing, transportation"},

    # Criminal Justice (5 cases)
    {"name": "Ex-Offender - Reentry Basics", "location": "Cedar Park, TX", "needs": "job placement, housing, legal services, substance abuse counseling, life skills"},
    {"name": "Formerly Incarcerated Parent - Reunification", "location": "Georgetown, TX", "needs": "parenting classes, housing, employment, family counseling, legal services"},
    {"name": "Probation - Compliance Support", "location": "Pflugerville, TX", "needs": "employment, housing, substance abuse treatment, mental health services, transportation"},
    {"name": "Sex Offender Registration - Housing", "location": "Kyle, TX", "needs": "housing assistance, legal guidance, employment, counseling, community reintegration"},
    {"name": "Jail-to-Community Transition", "location": "San Marcos, TX", "needs": "transitional housing, job readiness, substance abuse treatment, healthcare, case management"},

    # Foster Care (5 cases)
    {"name": "Youth Aging Out - Independence", "location": "Austin, TX", "needs": "housing, college scholarships, job readiness, life skills, mentorship"},
    {"name": "Foster Youth - Educational Advocacy", "location": "Round Rock, TX", "needs": "education support, tutoring, college prep, scholarships, mentorship"},
    {"name": "Kinship Foster Care", "location": "Cedar Park, TX", "needs": "financial assistance, legal support, respite care, counseling, support groups"},
    {"name": "Sibling Group - Adoption Support", "location": "Georgetown, TX", "needs": "adoption assistance, family support, counseling, financial resources, sibling programs"},
    {"name": "Foster Parent - Crisis Support", "location": "Pflugerville, TX", "needs": "respite care, crisis intervention, counseling, training, support groups"},

    # Mental Health (5 cases)
    {"name": "Severe Mental Illness - Crisis", "location": "Kyle, TX", "needs": "crisis intervention, psychiatric care, housing, case management, medication support"},
    {"name": "Opioid Addiction - Recovery", "location": "San Marcos, TX", "needs": "medication-assisted treatment, counseling, housing, job training, peer support"},
    {"name": "Dual Diagnosis - Integrated Treatment", "location": "Leander, TX", "needs": "mental health treatment, substance abuse counseling, housing, employment, case management"},
    {"name": "Youth Mental Health - Early Intervention", "location": "Bastrop, TX", "needs": "therapy, family counseling, school support, medication management, peer groups"},
    {"name": "Suicide Prevention - High Risk", "location": "Austin, TX (West)", "needs": "crisis hotline, emergency psychiatric care, safety planning, counseling, hospitalization"},
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
print("\n" + "=" * 80)
print("COMPREHENSIVE STATISTICAL ANALYSIS (50 prompts)")
print("=" * 80 + "\n")

chatgpt_successful = [r for r in chatgpt_results if r["success"]]
gemini_successful = [r for r in gemini_results if r["success"]]

if chatgpt_successful and gemini_successful:
    chatgpt_durations = [r["duration"] for r in chatgpt_successful]
    gemini_durations = [r["duration"] for r in gemini_successful]

    print(f"ChatGPT 5.1 (no reasoning) WITHOUT WEB SEARCH:")
    print(f"  Successful: {len(chatgpt_successful)}/{len(test_cases)}")
    print(f"  Average: {statistics.mean(chatgpt_durations):.2f}s")
    print(f"  Median: {statistics.median(chatgpt_durations):.2f}s")
    print(f"  Min: {min(chatgpt_durations):.2f}s")
    print(f"  Max: {max(chatgpt_durations):.2f}s")
    if len(chatgpt_durations) > 1:
        print(f"  Std Dev: {statistics.stdev(chatgpt_durations):.2f}s")
        print(f"  Variance: {statistics.variance(chatgpt_durations):.2f}")
    print()

    print(f"Gemini 3 Flash WITHOUT WEB SEARCH:")
    print(f"  Successful: {len(gemini_successful)}/{len(test_cases)}")
    print(f"  Average: {statistics.mean(gemini_durations):.2f}s")
    print(f"  Median: {statistics.median(gemini_durations):.2f}s")
    print(f"  Min: {min(gemini_durations):.2f}s")
    print(f"  Max: {max(gemini_durations):.2f}s")
    if len(gemini_durations) > 1:
        print(f"  Std Dev: {statistics.stdev(gemini_durations):.2f}s")
        print(f"  Variance: {statistics.variance(gemini_durations):.2f}")
    print()

    # Distribution Analysis
    if len(chatgpt_durations) >= 4:
        chatgpt_sorted = sorted(chatgpt_durations)
        gemini_sorted = sorted(gemini_durations)

        p25_idx = len(chatgpt_sorted) // 4
        p75_idx = (3 * len(chatgpt_sorted)) // 4
        p95_idx = int(0.95 * len(chatgpt_sorted))

        print(f"Distribution Analysis:")
        print(f"  ChatGPT 25th percentile: {chatgpt_sorted[p25_idx]:.2f}s")
        print(f"  ChatGPT 75th percentile: {chatgpt_sorted[p75_idx]:.2f}s")
        print(f"  ChatGPT 95th percentile: {chatgpt_sorted[p95_idx]:.2f}s")
        print()
        print(f"  Gemini 25th percentile: {gemini_sorted[p25_idx]:.2f}s")
        print(f"  Gemini 75th percentile: {gemini_sorted[p75_idx]:.2f}s")
        print(f"  Gemini 95th percentile: {gemini_sorted[p95_idx]:.2f}s")
        print()

    # Winner
    chatgpt_avg = statistics.mean(chatgpt_durations)
    gemini_avg = statistics.mean(gemini_durations)

    if gemini_avg < chatgpt_avg:
        speedup = ((chatgpt_avg / gemini_avg) - 1) * 100
        time_diff = chatgpt_avg - gemini_avg
        time_saved = time_diff * 1000 / 60
        print(f"🏆 WINNER: Gemini 3 Flash")
        print(f"   {speedup:.1f}% faster on average")
        print(f"   {time_diff:.2f}s faster per request")
        print(f"   ({gemini_avg:.2f}s vs {chatgpt_avg:.2f}s)")
        print(f"   Time saved on 1000 requests: {time_saved:.1f} minutes")
    else:
        speedup = ((gemini_avg / chatgpt_avg) - 1) * 100
        time_diff = gemini_avg - chatgpt_avg
        time_saved = time_diff * 1000 / 60
        print(f"🏆 WINNER: ChatGPT 5.1 (no reasoning)")
        print(f"   {speedup:.1f}% faster on average")
        print(f"   {time_diff:.2f}s faster per request")
        print(f"   ({chatgpt_avg:.2f}s vs {gemini_avg:.2f}s)")
        print(f"   Time saved on 1000 requests: {time_saved:.1f} minutes")

    print("=" * 80)
else:
    print("❌ Not enough successful results for comparison")
    print(f"ChatGPT successful: {len(chatgpt_successful)}/{len(test_cases)}")
    print(f"Gemini successful: {len(gemini_successful)}/{len(test_cases)}")
