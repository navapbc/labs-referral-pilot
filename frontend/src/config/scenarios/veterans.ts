import { ScenarioConfig } from "./index";

export const veteransScenario: ScenarioConfig = {
  id: "veterans",
  name: "Veteran Resource Navigator",
  tagline: "Connecting veterans with earned benefits and services",
  logoEmoji: "🎖️",
  primaryColor: "blue",
  categories: [
    { id: "va-healthcare", label: "VA Healthcare", emoji: "🏥" },
    { id: "mental-health", label: "Mental Health & PTSD", emoji: "🧠" },
    { id: "disability", label: "Disability Compensation", emoji: "📋" },
    { id: "education", label: "Education Benefits", emoji: "🎓" },
    { id: "employment", label: "Employment Assistance", emoji: "💼" },
    { id: "housing", label: "Housing Programs", emoji: "🏠" },
    { id: "caregiver", label: "Caregiver Support", emoji: "🤝" },
    { id: "legal", label: "Legal Services", emoji: "⚖️" },
    { id: "state-benefits", label: "State Veteran Benefits", emoji: "📍" },
    { id: "vet-centers", label: "Vet Centers", emoji: "🏢" },
    { id: "community-care", label: "Community Care", emoji: "👥" },
    { id: "financial", label: "Financial Assistance", emoji: "💵" },
  ],
  providerTypes: [
    { id: "va", label: "VA Programs", emoji: "🏛️" },
    { id: "state", label: "State Veteran Services", emoji: "📍" },
    { id: "vso", label: "Veteran Service Orgs", emoji: "🎖️" },
  ],
  sampleClientDescription:
    "Iraq veteran, 35, recently separated. Service-connected PTSD, 30% disability rating. Looking for employment but struggling with transition. Interested in using GI Bill. Currently staying with family, needs own housing.",
  sampleLocation: "San Diego, CA 92101",
  placeholderText:
    "Example: Post-9/11 veteran seeking healthcare enrollment and education benefits...",
  mockResources: [
    {
      name: "VA San Diego Healthcare System",
      addresses: ["3350 La Jolla Village Drive, San Diego, CA 92161"],
      phones: ["(858) 552-8585"],
      website: "https://www.va.gov/san-diego-health-care/",
      description:
        "Full-service VA medical center providing comprehensive healthcare including primary care, specialty care, mental health services, and PTSD treatment programs.",
      justification:
        "Client has service-connected PTSD. VA healthcare provides specialized PTSD treatment at no cost for service-connected conditions.",
      referral_type: "government",
    },
    {
      name: "San Diego Vet Center",
      addresses: ["2900 6th Ave, San Diego, CA 92103"],
      phones: ["(619) 294-2040"],
      website: "https://www.va.gov/vet-center/",
      description:
        "Community-based counseling centers providing readjustment services including individual and group counseling, family support, and employment assistance. Walk-ins welcome.",
      justification:
        "Vet Centers specialize in transition support and PTSD counseling in a more informal setting than VA hospitals. Good for recently separated veterans.",
      referral_type: "government",
    },
    {
      name: "VET TEC - IT Training",
      addresses: ["Multiple approved training providers"],
      phones: ["1-888-442-4551"],
      website:
        "https://www.va.gov/education/about-gi-bill-benefits/how-to-use-benefits/vettec-high-tech-program/",
      description:
        "VA program covering full tuition for high-tech training programs in computer programming, data processing, and IT. Includes housing allowance during training.",
      justification:
        "Fast-track alternative to GI Bill for tech careers. Client interested in education and this provides quicker path to employment with housing stipend.",
      referral_type: "government",
    },
    {
      name: "SSVF - Supportive Services for Veteran Families",
      addresses: ["Veterans Village of San Diego, 4141 Pacific Highway"],
      phones: ["(619) 497-0142"],
      website: "https://www.va.gov/homeless/ssvf/",
      description:
        "Rapid rehousing and homeless prevention for veterans and their families. Provides security deposits, short-term rental assistance, and case management.",
      justification:
        "Client staying with family and needs own housing. SSVF can provide security deposit, first month rent, and ongoing support.",
      referral_type: "government",
    },
    {
      name: "Hire Heroes USA",
      addresses: ["Virtual services available"],
      phones: ["(844) 634-1520"],
      website: "https://www.hireheroesusa.org",
      description:
        "Free career coaching, resume assistance, and job matching for transitioning service members and veterans. Personalized one-on-one support.",
      justification:
        "Client struggling with transition to civilian employment. Hire Heroes provides dedicated career coach to help translate military experience.",
      referral_type: "external",
    },
    {
      name: "DAV - Disabled American Veterans",
      addresses: ["DAV San Diego Chapter, San Diego, CA"],
      phones: ["(619) 400-5320"],
      website: "https://www.dav.org",
      description:
        "Free claims assistance for VA disability benefits. Accredited representatives help veterans file and appeal disability claims.",
      justification:
        "Client has 30% rating but may qualify for higher rating. DAV can review for additional service-connected conditions.",
      referral_type: "external",
    },
  ],
  mockActionPlan: {
    title: "Your Veteran Transition Action Plan",
    summary:
      "Thank you for your service. Here's a coordinated plan to get you stable housing, continue your PTSD care, and launch your civilian career using the benefits you've earned.",
    content: `## 🏥 Priority 1: Connect with Mental Health Support (This Week)

**Your 30% PTSD rating means you've earned these services at NO cost to you.**

**Option A: VA San Diego Mental Health**
- Call **(858) 552-8585**, ask for Mental Health Clinic
- Specialized PTSD treatment programs available
- Can prescribe medication if helpful

**Option B: Vet Center (More Casual Setting)**
- Walk in at **2900 6th Ave, San Diego** or call **(619) 294-2040**
- Individual counseling, group sessions with other combat vets
- Also helps with transition issues, employment, family concerns
- **No VA enrollment required**

**Recommendation:** Start with the Vet Center—it's designed for recently separated vets and has less bureaucracy. You can always add VA care later.

## 🏠 Priority 2: Get Your Own Housing (Start Within 1 Week)

**SSVF can help you move from your family's place to your own apartment.**

**What to do:**
- Call Veterans Village of San Diego: **(619) 497-0142**
- Ask about SSVF housing assistance
- They can provide:
  - Security deposit (often $1,500-2,500)
  - First month's rent
  - Utility deposits
  - Ongoing case management

**What you'll need:**
- DD-214 (discharge paperwork)
- ID
- Proof of income (VA disability, any other income)

**Timeline:** Most veterans find housing within 2-4 weeks with SSVF support.

## 🎓 Priority 3: Choose Your Education/Training Path (Within 2 Weeks)

**You have two excellent options:**

### Option A: VET TEC (Faster Path to Tech Career)
**Best if:** You want to work in IT/tech and want to start earning ASAP

- **Duration:** 3-6 months depending on program
- **Cost:** $0 (VA covers full tuition)
- **Housing allowance:** Yes! Full BAH rate during training
- **Programs:** Coding bootcamps, cybersecurity, data analytics

**To apply:** va.gov/education/about-gi-bill-benefits/how-to-use-benefits/vettec-high-tech-program/

### Option B: Post-9/11 GI Bill (Traditional Education)
**Best if:** You want a degree for long-term career

- **Duration:** Up to 36 months of benefits
- **Covers:** Tuition, housing allowance, book stipend
- **Options:** University, community college, trade schools

**Important:** VET TEC does NOT use up your GI Bill—you could do VET TEC first, then GI Bill later!

## 💼 Priority 4: Launch Your Job Search (Start Within 2 Weeks)

**Even while training, start building your civilian career foundation.**

**Step 1: Get a career coach (FREE)**
- Call Hire Heroes USA: **(844) 634-1520**
- They'll assign you a dedicated coach
- Help translating military skills to civilian resume
- Job matching and interview prep

**Step 2: Attend a hiring event**
- Check hireveterans.com for San Diego events
- Many employers specifically recruit veterans

## 📋 Priority 5: Review Your Disability Rating (Within 30 Days)

**You may be underrated.** Many veterans with PTSD and combat service have additional service-connected conditions.

**What to do:**
- Call DAV San Diego: **(619) 400-5320**
- Ask for a free claims review
- They can identify conditions you may have missed
- **Higher ratings = more monthly compensation**

**Example:** If additional conditions increase you from 30% to 50%, your monthly compensation increases from ~$508 to ~$1,041.

## 📅 Your First Month Timeline

| Week | Actions |
|------|---------|
| **Week 1** | - Call Vet Center for counseling<br>- Call SSVF for housing help |
| **Week 2** | - Apply for VET TEC or GI Bill<br>- Register with Hire Heroes USA |
| **Week 3** | - Tour housing options with SSVF<br>- Begin training research |
| **Week 4** | - Sign lease (with SSVF assistance)<br>- Schedule DAV claims review |

---

**Questions about your benefits?** Call the VA at **1-800-827-1000** or visit your local Vet Center for help navigating the system.`,
  },
};
