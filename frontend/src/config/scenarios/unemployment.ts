import { ScenarioConfig } from "./index";

export const unemploymentScenario: ScenarioConfig = {
  id: "unemployment",
  name: "Career Transition Navigator",
  tagline: "Resources to support your path back to work",
  logoEmoji: "💼",
  primaryColor: "indigo",
  categories: [
    { id: "training", label: "Job Training Programs", emoji: "🎓" },
    { id: "resume", label: "Resume & Interview Help", emoji: "📄" },
    { id: "counseling", label: "Career Counseling", emoji: "🧭" },
    { id: "healthcare", label: "Healthcare Coverage", emoji: "🩺" },
    { id: "rent", label: "Emergency Rent Assistance", emoji: "🏠" },
    { id: "utility", label: "Utility Assistance", emoji: "💡" },
    { id: "food", label: "Food Assistance", emoji: "🍽️" },
    { id: "childcare", label: "Childcare for Job Seekers", emoji: "👶" },
    { id: "transportation", label: "Transportation Help", emoji: "🚗" },
    { id: "mental-health", label: "Mental Health Support", emoji: "🧠" },
    { id: "small-business", label: "Small Business Resources", emoji: "🏪" },
    { id: "financial", label: "Financial Counseling", emoji: "💵" },
  ],
  providerTypes: [
    { id: "workforce", label: "Workforce Development", emoji: "💼" },
    { id: "government", label: "Government Programs", emoji: "🏛️" },
    { id: "community", label: "Community Services", emoji: "👥" },
  ],
  sampleClientDescription:
    "45-year-old laid off from manufacturing job after 15 years. Receiving UI benefits but worried about healthcare (was on employer plan). Interested in retraining for IT. Has car payment and mortgage.",
  sampleLocation: "Newark, NJ 07102",
  placeholderText:
    "Example: Recently laid off from retail job, looking for career change, concerned about bills...",
  mockResources: [
    {
      name: "WIOA IT Training Program - Rutgers",
      addresses: ["Rutgers Continuing Education, Newark, NJ"],
      phones: ["(973) 353-5000"],
      website: "https://ce.rutgers.edu",
      description:
        "Workforce Innovation and Opportunity Act funded technology training programs including CompTIA certifications, cybersecurity, and coding bootcamps. Tuition covered for eligible participants.",
      justification:
        "Client expressed interest in IT retraining. WIOA can fund full tuition for career changers receiving unemployment.",
      referral_type: "government",
    },
    {
      name: "NJ Health Insurance Marketplace",
      addresses: ["GetCoveredNJ - Online enrollment"],
      phones: ["1-833-677-1010"],
      website: "https://www.getcovered.nj.gov",
      description:
        "State health insurance marketplace offering ACA plans. Job loss triggers special enrollment period. Subsidies available based on income.",
      justification:
        "Client lost employer health coverage. Qualifies for special enrollment period and likely eligible for premium subsidies on UI income.",
      referral_type: "government",
    },
    {
      name: "Newark One-Stop Career Center",
      addresses: ["990 Broad Street, Newark, NJ 07102"],
      phones: ["(973) 648-3370"],
      website: "https://www.nj.gov/labor/career-services/",
      description:
        "Comprehensive career services including resume workshops, interview coaching, job matching, and access to training funds. Free for all NJ residents.",
      justification:
        "Provides immediate career counseling and can connect client to training funds while exploring IT career transition.",
      referral_type: "government",
    },
    {
      name: "Emergency Mortgage Assistance - NJ HMFA",
      addresses: ["NJ Housing and Mortgage Finance Agency"],
      phones: ["1-800-654-6873"],
      website: "https://www.nj.gov/dca/hmfa",
      description:
        "State program providing emergency mortgage assistance to homeowners facing financial hardship. Can provide up to 6 months of assistance.",
      justification:
        "Client has mortgage and recently lost income. Emergency assistance can prevent default while in training/job search.",
      referral_type: "government",
    },
    {
      name: "Community FoodBank of New Jersey",
      addresses: ["31 Evans Terminal, Hillside, NJ 07205"],
      phones: ["(908) 355-3663"],
      website: "https://cfbnj.org",
      description:
        "Network of food pantries and meal programs throughout New Jersey. Also offers SNAP application assistance.",
      justification:
        "Can supplement food budget while income is reduced, allowing client to focus resources on housing and healthcare.",
      referral_type: "external",
    },
  ],
  mockActionPlan: {
    title: "Your Career Transition Action Plan",
    summary:
      "You have 15 years of valuable experience. Here's a strategic plan to transition into IT while protecting your home and health coverage during the process.",
    content: `## 🏥 Priority 1: Secure Health Insurance (This Week)

**Why urgent:** You have a 60-day Special Enrollment Period from job loss. Don't wait!

**What to do:**
- Go to **GetCovered.NJ.gov** or call **1-833-677-1010**
- Have ready: Job termination date, household income (UI benefits count)
- Compare plans—with UI income, you likely qualify for significant subsidies

**Cost estimate:** With $600/week UI benefits (~$31K annual), you may qualify for plans as low as $50-150/month with subsidies.

**Deadline:** Enroll within 60 days of losing employer coverage to avoid a gap.

## 🏠 Priority 2: Protect Your Mortgage (Within 2 Weeks)

**Why this matters:** Don't wait until you're behind. Assistance is easier to get BEFORE you miss payments.

**What to do:**
- Call NJ HMFA at **1-800-654-6873**
- Ask about the Homeowner Assistance Fund
- Can provide up to 6 months of mortgage assistance

**Also contact your lender:** Many offer forbearance programs for unemployed homeowners. A quick call now can prevent problems later.

## 🎓 Priority 3: Start IT Training Path (Within 2 Weeks)

**Your goal:** Use this transition to build new skills. WIOA funding can cover your entire training.

**Step A: Visit Newark One-Stop Career Center**
- Address: 990 Broad Street, Newark, NJ 07102
- Call **(973) 648-3370** for appointment
- Bring: ID, resume, UI documentation

**Step B: Get approved for WIOA funding**
- As a dislocated worker, you qualify for training funds
- WIOA can pay for certifications, bootcamps, even degree programs
- Training stipend may also be available

**Step C: Enroll in IT training at Rutgers**
- Contact: **(973) 353-5000** or ce.rutgers.edu
- Options include: CompTIA A+, Network+, Security+, coding bootcamps
- Many programs complete in 3-6 months

**Timeline for IT career:**
| Month 1-2 | Get WIOA approved, start CompTIA A+ |
| Month 3-4 | Complete A+, start Network+ or Security+ |
| Month 5-6 | Complete certs, begin job search |
| Target | Entry IT support role: $45-60K salary |

## 🍽️ Priority 4: Reduce Living Expenses (Ongoing)

**Stretch your UI benefits further:**

- **Food Bank:** Visit cfbnj.org for free groceries while in transition
- **Utility assistance:** If heating/electric is a strain, ask about LIHEAP
- **Car payment:** Contact your lender about temporary payment reduction

## 📅 Your Weekly Checklist

**Week 1:**
- [ ] Apply for health insurance through GetCovered.NJ
- [ ] Call NJ HMFA about mortgage assistance
- [ ] Schedule One-Stop Career Center appointment

**Week 2:**
- [ ] Attend One-Stop Career Center appointment
- [ ] Begin WIOA training approval process
- [ ] Visit local food bank

**Week 3-4:**
- [ ] Finalize WIOA funding approval
- [ ] Enroll in IT training program
- [ ] Set up study schedule

---

**Your One-Stop Career Center counselor can help coordinate all of this.** Call **(973) 648-3370** to get started.`,
  },
};
