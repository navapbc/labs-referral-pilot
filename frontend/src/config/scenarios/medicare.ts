import { ScenarioConfig } from "./index";

export const medicareScenario: ScenarioConfig = {
  id: "medicare",
  name: "Medicare Resource Navigator",
  tagline: "Connecting beneficiaries with support services",
  logoEmoji: "🏥",
  primaryColor: "blue",
  categories: [
    { id: "msp", label: "Medicare Savings Programs", emoji: "💳" },
    { id: "prescription", label: "Prescription Assistance", emoji: "💊" },
    { id: "transportation", label: "Transportation", emoji: "🚗" },
    { id: "home-health", label: "Home Health Services", emoji: "🏠" },
    { id: "chronic", label: "Chronic Disease Management", emoji: "❤️" },
    { id: "nutrition", label: "Nutrition Programs", emoji: "🍽️" },
    { id: "caregiver", label: "Caregiver Support", emoji: "🤝" },
    { id: "dme", label: "Medical Equipment", emoji: "🦽" },
    { id: "mental-health", label: "Mental Health Services", emoji: "🧠" },
    { id: "ltc", label: "Long-Term Care Options", emoji: "🏢" },
    { id: "dental-vision", label: "Dental & Vision", emoji: "👁️" },
    { id: "social", label: "Social & Recreation", emoji: "👥" },
  ],
  providerTypes: [
    { id: "medicare", label: "Medicare/CMS", emoji: "🏛️" },
    { id: "state", label: "State Programs", emoji: "📋" },
    { id: "community", label: "Community Organizations", emoji: "👥" },
  ],
  sampleClientDescription:
    "78-year-old Medicare beneficiary on fixed income (~$1,400/month Social Security). Recently diagnosed with diabetes. Struggling to afford medications and needs help getting to doctor appointments. Lives alone, limited mobility.",
  sampleLocation: "Philadelphia, PA 19103",
  placeholderText:
    "Example: 72-year-old on Medicare with heart condition, needs help affording medications and getting to appointments...",
  mockResources: [
    {
      name: "Medicare Extra Help (Low Income Subsidy)",
      addresses: ["Social Security Administration - Philadelphia Office"],
      phones: ["1-800-772-1213"],
      website: "https://www.ssa.gov/medicare/part-d-extra-help",
      description:
        "Federal program that helps Medicare beneficiaries with limited income pay for prescription drug costs. Can save up to $5,000/year on medications.",
      justification:
        "With income of $1,400/month, client likely qualifies for Extra Help which would significantly reduce diabetes medication costs.",
      referral_type: "government",
    },
    {
      name: "PA PACE/PACENET",
      addresses: [
        "Pennsylvania Department of Aging, 555 Walnut St, Harrisburg, PA",
      ],
      phones: ["1-800-225-7223"],
      website: "https://www.aging.pa.gov/aging-services/prescriptions",
      description:
        "Pennsylvania's prescription assistance programs for older adults. PACE covers most prescription costs with small copays.",
      justification:
        "State pharmaceutical assistance program that works alongside Medicare to further reduce medication costs for PA residents.",
      referral_type: "government",
    },
    {
      name: "Philadelphia Corporation for Aging - Transportation",
      addresses: ["642 N Broad St, Philadelphia, PA 19130"],
      phones: ["(215) 765-9040"],
      website: "https://www.pcacares.org",
      description:
        "Area Agency on Aging providing transportation services to medical appointments for seniors 60+ through volunteer drivers and transit subsidies.",
      justification:
        "Directly addresses transportation needs for doctor appointments. Can arrange recurring rides for diabetes management visits.",
      referral_type: "external",
    },
    {
      name: "Diabetes Self-Management Program",
      addresses: ["Thomas Jefferson University Hospital, Philadelphia, PA"],
      phones: ["(215) 955-6000"],
      website: "https://www.jeffersonhealth.org",
      description:
        "6-week evidence-based program teaching diabetes management skills including nutrition, exercise, medication management, and blood sugar monitoring.",
      justification:
        "Client was recently diagnosed with diabetes and would benefit from structured education on managing the condition.",
      referral_type: "external",
    },
    {
      name: "Meals on Wheels - Philadelphia",
      addresses: ["PCA Meals on Wheels, Philadelphia, PA"],
      phones: ["(215) 765-9040"],
      website: "https://www.pcacares.org/services/meals-on-wheels",
      description:
        "Home-delivered nutritious meals for homebound seniors, including diabetic-friendly meal options. Also provides daily wellness checks.",
      justification:
        "Living alone with limited mobility, client would benefit from delivered meals with diabetes-appropriate nutrition.",
      referral_type: "external",
    },
  ],
  mockActionPlan: {
    title: "Your Medicare Benefits Action Plan",
    summary:
      "Based on your situation, here's a prioritized plan to help you reduce medication costs, get to appointments, and manage your diabetes effectively.",
    content: `## Step 1: Apply for Extra Help (This Week)

**Why this is urgent:** Extra Help can save you up to $5,000/year on prescriptions. With your income of $1,400/month, you likely qualify automatically.

**What to do:**
- Call Social Security at **1-800-772-1213** (TTY 1-800-325-0778)
- Or apply online at ssa.gov/medicare/part-d-extra-help
- Have ready: Your Medicare card, proof of income, and bank statements

**What to expect:** Processing takes about 2-3 weeks. Once approved, your pharmacy will see your new lower copays automatically.

## Step 2: Enroll in PA PACE (Within 2 Weeks)

**Why this helps:** PACE works alongside Medicare to further reduce your prescription costs. You may pay as little as $6-$9 per prescription.

**What to do:**
- Call **1-800-225-7223** to check eligibility
- They can enroll you over the phone
- Bring your Medicare card number and income information

## Step 3: Set Up Medical Transportation (This Week)

**Why this matters:** Regular diabetes check-ups are essential. PCA provides free rides to medical appointments.

**What to do:**
- Call PCA at **(215) 765-9040**
- Ask about the Shared Ride program for medical appointments
- Schedule recurring rides for your upcoming doctor visits

**Tip:** Book rides at least 2 days in advance for best availability.

## Step 4: Enroll in Diabetes Self-Management (Within 30 Days)

**Why this helps:** Learning to manage diabetes can prevent complications and reduce long-term healthcare costs.

**What to do:**
- Call Jefferson Hospital at **(215) 955-6000**
- Ask about the free Diabetes Self-Management Program
- The 6-week program meets once weekly

**Medicare covers this program at no cost to you.**

## Step 5: Apply for Meals on Wheels (Within 2 Weeks)

**Why this helps:** Regular, diabetes-friendly meals support your health and provide a daily check-in.

**What to do:**
- Call PCA at **(215) 765-9040**
- Ask about Meals on Wheels for diabetic meal options
- Service typically starts within 1-2 weeks of enrollment

---

**Questions?** Your Medicare counselor at the Philadelphia Corporation for Aging can help you navigate these programs: **(215) 765-9040**`,
  },
};
