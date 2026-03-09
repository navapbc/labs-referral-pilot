import { ScenarioConfig } from "./index";

export const pfmlScenario: ScenarioConfig = {
  id: "pfml",
  name: "PFML Support Navigator",
  tagline: "Resources during your leave and beyond",
  logoEmoji: "👨‍👩‍👧",
  primaryColor: "purple",
  categories: [
    { id: "healthcare", label: "Healthcare Providers", emoji: "🩺" },
    { id: "mental-health", label: "Mental Health Services", emoji: "🧠" },
    { id: "new-parent", label: "New Parent Resources", emoji: "👶" },
    { id: "caregiver", label: "Caregiver Support", emoji: "🤝" },
    { id: "financial", label: "Financial Counseling", emoji: "💵" },
    { id: "childcare", label: "Childcare", emoji: "🏫" },
    { id: "lactation", label: "Lactation Support", emoji: "🍼" },
    { id: "physical-therapy", label: "Physical Therapy", emoji: "🏃" },
    { id: "chronic-illness", label: "Chronic Illness Support", emoji: "❤️" },
    { id: "return-to-work", label: "Return-to-Work", emoji: "💼" },
    { id: "legal", label: "Workplace Rights", emoji: "⚖️" },
    { id: "support-groups", label: "Support Groups", emoji: "👥" },
  ],
  providerTypes: [
    { id: "healthcare", label: "Healthcare Services", emoji: "🏥" },
    { id: "state", label: "State Programs", emoji: "🏛️" },
    { id: "community", label: "Community Support", emoji: "👥" },
  ],
  sampleClientDescription:
    "New mother on 12-week PFML leave. First child, feeling overwhelmed. Looking for breastfeeding support and postpartum mental health resources. Worried about affording childcare when returning to work.",
  sampleLocation: "Boston, MA 02108",
  placeholderText:
    "Example: Taking medical leave for surgery, need help finding physical therapy and managing recovery...",
  mockResources: [
    {
      name: "WIC - Women, Infants, and Children",
      addresses: ["Boston Public Health Commission WIC Program"],
      phones: ["(617) 534-5050"],
      website: "https://www.mass.gov/wic",
      description:
        "Nutrition program providing breastfeeding support, peer counselors, breast pumps, and supplemental foods for pregnant and postpartum women and children under 5.",
      justification:
        "Client seeking breastfeeding support. WIC provides free lactation consultants, breast pumps, and ongoing peer support.",
      referral_type: "government",
    },
    {
      name: "Postpartum Support International - MA Chapter",
      addresses: ["Virtual support groups and helpline"],
      phones: ["1-800-944-4773"],
      website: "https://www.postpartum.net/get-help/locations/massachusetts/",
      description:
        "Free support groups, peer mentors, and resources for postpartum depression and anxiety. Includes specialized groups for new mothers.",
      justification:
        "Client feeling overwhelmed as first-time mother. PSI offers peer support groups specifically for new parents experiencing adjustment difficulties.",
      referral_type: "external",
    },
    {
      name: "Mass General Lactation Services",
      addresses: ["55 Fruit Street, Boston, MA 02114"],
      phones: ["(617) 726-2229"],
      website: "https://www.massgeneral.org/obstetrics/lactation",
      description:
        "Board-certified lactation consultants providing individual consultations, group classes, and phone support. Most insurance plans cover visits.",
      justification:
        "Hospital-based lactation support for breastfeeding challenges. Insurance typically covers consultations during postpartum period.",
      referral_type: "external",
    },
    {
      name: "Child Care Financial Assistance (CCFA)",
      addresses: ["MA Department of Early Education and Care"],
      phones: ["(617) 988-6600"],
      website: "https://www.mass.gov/child-care-financial-assistance-ccfa",
      description:
        "State childcare subsidies for working families. Income-eligible families pay reduced copays based on family size and income.",
      justification:
        "Client worried about childcare costs when returning to work. CCFA can significantly reduce childcare expenses.",
      referral_type: "government",
    },
    {
      name: "Employee Assistance Program (EAP)",
      addresses: ["Contact employer HR for specific EAP provider"],
      phones: ["Varies by employer"],
      description:
        "Most employers offer free, confidential counseling through EAP. Typically includes 3-8 free sessions for mental health, stress, family issues.",
      justification:
        "Free short-term counseling available through employer. Good first step for postpartum mental health support before seeking ongoing care.",
      referral_type: "external",
    },
    {
      name: "Boston Parent Support Group - First-Time Parents",
      addresses: ["Various community centers in Boston"],
      phones: ["(617) 474-1143"],
      website: "https://familynurturing.org",
      description:
        "Free weekly support groups for new parents facilitated by trained parent educators. Includes discussions, resources, and peer connection.",
      justification:
        "First-time parent feeling overwhelmed. Parent support groups provide community and normalize challenges of new parenthood.",
      referral_type: "external",
    },
  ],
  mockActionPlan: {
    title: "Your New Parent Support Plan",
    summary:
      "Congratulations on your new baby! Feeling overwhelmed is completely normal. Here's a plan to get you the breastfeeding support, mental health resources, and childcare help you need.",
    content: `## 💚 First: You're Doing Great

Feeling overwhelmed as a first-time parent is **completely normal**. About 1 in 5 new mothers experience postpartum mood changes. Reaching out for support is a sign of strength, not weakness.

## 🍼 Priority 1: Breastfeeding Support (This Week)

**If breastfeeding is challenging, help is available:**

### Option A: WIC (Free, includes more than just food!)
- Call **(617) 534-5050** for Boston WIC
- Services include:
  - **Free breast pump** (electric or manual)
  - **Peer breastfeeding counselors** who've been there
  - **Lactation consultants** at no cost
  - Supplemental food for you and baby
- **You likely qualify** based on pregnancy/postpartum status

### Option B: Mass General Lactation Services
- Call **(617) 726-2229**
- Board-certified lactation consultants
- Individual appointments and group classes
- **Usually covered by insurance** during postpartum period

**Tip:** Many breastfeeding challenges can be solved in just 1-2 sessions with an IBCLC (lactation consultant).

## 🧠 Priority 2: Mental Health Support (Start This Week)

**You deserve support. These resources are confidential and judgment-free.**

### Immediate Support: Postpartum Support International
- **Helpline:** 1-800-944-4773 (available daily)
- **Text:** 1-800-944-4773
- Free virtual support groups specifically for new moms
- Peer mentors who've experienced postpartum challenges

### Ongoing Support Options:

**Option A: Your Employer's EAP**
- Contact HR for your EAP provider information
- Typically **3-8 FREE sessions** included
- Confidential—employer never knows you used it
- Can start immediately, no referral needed

**Option B: Boston Parent Support Group**
- Call **(617) 474-1143** or visit familynurturing.org
- Free weekly groups for first-time parents
- Meet other parents going through the same thing
- In-person connection and community

## 👶 Priority 3: Plan for Childcare (Start 4-6 Weeks Before Return)

**Don't wait until the last minute—quality childcare has waitlists!**

### Step 1: Apply for Financial Assistance
- Call **(617) 988-6600** for Child Care Financial Assistance (CCFA)
- Based on income, you may qualify for subsidized care
- **Apply now** even if you're still on leave—approval takes time

### Step 2: Research Providers
- Visit mass.gov/childcare to search licensed providers
- Tour at least 3 options before deciding
- Ask about:
  - Infant care availability (often limited)
  - Hours and flexibility
  - Communication with parents
  - Staff-to-child ratios

### Step 3: Get on Waitlists
- Good infant care programs often have 3-6 month waitlists
- Get on multiple waitlists to increase options

## 📅 Your Weekly Wellness Checklist

**Every new parent should:**

- [ ] **Sleep when baby sleeps** (even 20 minutes helps)
- [ ] **Accept help** from family/friends who offer
- [ ] **Get outside** for at least 10 minutes daily
- [ ] **Connect with another adult** daily (text counts!)
- [ ] **Eat regular meals** (even if simple)

## ⚠️ When to Seek Immediate Help

Contact your provider or call 988 (Suicide & Crisis Lifeline) if you experience:
- Thoughts of harming yourself or baby
- Inability to sleep even when baby sleeps
- Severe anxiety or panic attacks
- Feeling disconnected from your baby

**These feelings are treatable. Help is available 24/7.**

## 📋 Before Your Leave Ends

| 6 Weeks Before | Start childcare search, apply for CCFA |
| 4 Weeks Before | Tour childcare options, get on waitlists |
| 2 Weeks Before | Confirm childcare, plan return-to-work schedule |
| 1 Week Before | Do trial run of morning routine |

---

**Remember:** Taking care of yourself IS taking care of your baby. You're not alone in this.

**MA PFML Questions?** Call **(833) 344-7365** or visit mass.gov/pfml`,
  },
};
