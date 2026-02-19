import { ScenarioConfig } from "./index";

export const snapScenario: ScenarioConfig = {
  id: "snap",
  name: "Benefits Connection Navigator",
  tagline: "One door to all the support you qualify for",
  logoEmoji: "🏢",
  primaryColor: "green",
  categories: [
    { id: "food", label: "Food Assistance", emoji: "🍽️" },
    { id: "healthcare", label: "Healthcare Coverage", emoji: "🩺" },
    { id: "utility", label: "Utility Assistance", emoji: "💡" },
    { id: "childcare", label: "Childcare Subsidies", emoji: "👶" },
    { id: "cash", label: "Cash Assistance", emoji: "💵" },
    { id: "housing", label: "Housing Help", emoji: "🏠" },
    { id: "employment", label: "Employment Services", emoji: "💼" },
    { id: "tax-credits", label: "Tax Credits", emoji: "📋" },
    { id: "school-meals", label: "School Meals", emoji: "🎒" },
    { id: "phone-internet", label: "Phone & Internet", emoji: "📱" },
    { id: "transportation", label: "Transportation", emoji: "🚗" },
    { id: "wic", label: "WIC", emoji: "🍼" },
  ],
  providerTypes: [
    { id: "federal", label: "Federal Programs", emoji: "🏛️" },
    { id: "state", label: "State Programs", emoji: "📋" },
    { id: "community", label: "Community Partners", emoji: "👥" },
  ],
  sampleClientDescription:
    "Single mother, 2 children (ages 3 and 7). Recently lost job, applying for SNAP. No health insurance for kids. Behind on electric bill. Needs childcare to look for work.",
  sampleLocation: "Lincoln, NE 68508",
  placeholderText:
    "Example: Family of 4, both parents working part-time, struggling to afford groceries and healthcare...",
  mockResources: [
    {
      name: "SNAP - Supplemental Nutrition Assistance Program",
      addresses: [
        "Nebraska DHHS, 301 Centennial Mall South, Lincoln, NE 68509",
      ],
      phones: ["1-800-383-4278"],
      website: "https://dhhs.ne.gov/Pages/Supplemental-Nutrition.aspx",
      description:
        "Federal nutrition program providing monthly benefits for food purchases. Expedited processing available for households with very low income or resources.",
      justification:
        "Client is already applying for SNAP. With recent job loss and children, likely qualifies for expedited benefits within 7 days.",
      referral_type: "government",
    },
    {
      name: "Medicaid / CHIP for Children",
      addresses: ["Nebraska DHHS - same application as SNAP"],
      phones: ["1-855-632-7633"],
      website: "https://dhhs.ne.gov/Pages/Medicaid-and-CHIP.aspx",
      description:
        "Free or low-cost health coverage for children. Kids' Connection covers children in families with income up to 218% of poverty level.",
      justification:
        "Children currently have no health insurance. Can apply simultaneously with SNAP using combined application.",
      referral_type: "government",
    },
    {
      name: "LIHEAP - Low Income Home Energy Assistance",
      addresses: ["Nebraska Energy Assistance, Lincoln Action Program"],
      phones: ["(402) 471-3121"],
      website: "https://dhhs.ne.gov/Pages/Energy-Assistance.aspx",
      description:
        "Federal program helping low-income households pay heating and cooling bills. Can prevent utility shutoffs and provide crisis assistance.",
      justification:
        "Client is behind on electric bill. LIHEAP can provide direct payment to utility company and prevent disconnection.",
      referral_type: "government",
    },
    {
      name: "Title XX Childcare Subsidy",
      addresses: ["Nebraska DHHS Childcare Subsidy Program"],
      phones: ["1-800-430-3244"],
      website: "https://dhhs.ne.gov/Pages/Child-Care-Subsidy-Program.aspx",
      description:
        "Helps low-income families pay for childcare so parents can work, look for work, or attend school/training. Copays based on income.",
      justification:
        "Client needs childcare to job search. With recent job loss, may qualify for transitional childcare assistance.",
      referral_type: "government",
    },
    {
      name: "TANF - Temporary Assistance for Needy Families",
      addresses: ["Nebraska DHHS - same office as SNAP"],
      phones: ["1-800-383-4278"],
      website: "https://dhhs.ne.gov/Pages/Aid-to-Dependent-Children.aspx",
      description:
        "Cash assistance for families with children while working toward self-sufficiency. Includes employment services and support.",
      justification:
        "As a single parent with young children and no current income, client may qualify for temporary cash assistance.",
      referral_type: "government",
    },
    {
      name: "Food Bank of Lincoln",
      addresses: ["4840 Doris Bair Circle, Suite A, Lincoln, NE 68504"],
      phones: ["(402) 466-8170"],
      website: "https://lincolnfoodbank.org",
      description:
        "Emergency food assistance through network of food pantries. No documentation required. Can provide immediate food while SNAP processes.",
      justification:
        "Provides immediate food assistance while SNAP application is being processed. Multiple locations throughout Lincoln.",
      referral_type: "external",
    },
  ],
  mockActionPlan: {
    title: "Your Integrated Benefits Action Plan",
    summary:
      "Good news: You can apply for multiple benefits at once! Here's your prioritized checklist to get your family the support you need as quickly as possible.",
    content: `## 🚨 Immediate Action: Food Bank Visit (Today/Tomorrow)

**Why now:** Your family needs food while benefits process. No appointment or documentation needed.

**What to do:**
- Visit Food Bank of Lincoln or any partner pantry
- Find locations at lincolnfoodbank.org or call **(402) 466-8170**
- Bring bags or boxes to carry food home

**What you'll get:** Enough food for your family for about a week.

## Step 1: Complete Combined Application (Within 3 Days)

**The good news:** Nebraska uses ONE application for SNAP, Medicaid, CHIP, and TANF. Apply once, get considered for all programs!

**What to do:**
- Apply online at **ACCESSNebraska.ne.gov**
- OR call **1-800-383-4278**
- OR visit your local DHHS office in person

**Documents to gather:**
- ✓ ID for you (driver's license or state ID)
- ✓ Social Security cards for you and children
- ✓ Proof of address (utility bill, lease)
- ✓ Proof of job loss (termination letter if available)
- ✓ Bank statements from last 30 days
- ✓ Children's birth certificates

**Ask for expedited SNAP:** With no income and children, you may qualify for SNAP within **7 days** instead of 30.

## Step 2: Address Utility Emergency (Within 3 Days)

**Why urgent:** Prevent disconnection before it happens.

**What to do:**
- Call Lincoln Action Program at **(402) 471-3121**
- Ask about LIHEAP emergency assistance
- They can make direct payment to your utility company

**Bring:** Your utility bill showing past-due amount, ID, and proof of income (or lack thereof).

## Step 3: Apply for Childcare Subsidy (Within 1 Week)

**Why this matters:** You need childcare to job search and interview. The state will help pay for it.

**What to do:**
- Call **1-800-430-3244** for Childcare Subsidy Program
- Explain you need childcare to look for work
- They'll help you find approved childcare providers

**What to expect:** While searching for work, you can get subsidized childcare. Once employed, copays are based on your income.

## 📋 Your Benefits Checklist

| Benefit | Timeline | Phone |
|---------|----------|-------|
| SNAP (expedited) | 7 days | 1-800-383-4278 |
| Medicaid/CHIP | 30-45 days | 1-855-632-7633 |
| LIHEAP | 1-2 weeks | (402) 471-3121 |
| Childcare Subsidy | 2-4 weeks | 1-800-430-3244 |
| TANF (if needed) | 30-45 days | 1-800-383-4278 |

## After You're Employed

Once you find work, remember:
- **Report income changes** within 10 days to keep benefits accurate
- **SNAP benefits adjust** gradually—you won't lose them immediately
- **Childcare subsidy continues** while you work (with income-based copay)
- **Medicaid may continue** for 12 months of transitional coverage

---

**Need help with your applications?** Nebraska DHHS has caseworkers who can help: **1-800-383-4278**`,
  },
};
