# Use Case Exploration: AI-Powered Resource Referral Tool

## Current State

The labs-referral-pilot is an AI-powered resource referral tool currently designed for **Goodwill career case managers**. It uses RAG (Retrieval Augmented Generation) to match client needs with relevant community resources and generates personalized action plans.

**Core Capabilities:**
- Natural language input describing client needs
- Location-based filtering (zip code or city/state)
- Category and provider type filtering
- AI-generated resource justifications explaining why each resource fits the client
- Structured action plan generation
- Print and email sharing options

---

## Use Cases Aligned with Nava's Mission

Nava works with federal, state, and local governments to improve public benefit delivery. The following use cases are prioritized based on alignment with Nava's existing partnerships and focus areas.

### Tier 1: Direct Alignment with Current Nava Work

#### 1. WIC Program Navigators
**Context:** Nava already works with Montana WIC on eligibility screening tools. WIC serves 6 million parents and children.

**Use Case:** Help WIC staff and community partners connect eligible families with complementary services:
- Breastfeeding support resources
- Pediatric healthcare providers accepting WIC
- Food banks and pantries
- Early childhood programs (Head Start, Early Head Start)
- Medicaid and CHIP enrollment assistance
- Housing assistance for families with young children

**Why It Fits:**
- Existing Nava relationship with WIC programs
- Similar workflow to current tool (intake → resource matching → action plan)
- Strong potential for warm handoff integration with WIC MIS systems

**Sources:** [CBPP: Digital Tools for WIC](https://www.cbpp.org/research/launching-new-digital-tools-for-wic-participants), [Nava: Montana WIC Case Study](https://www.navapbc.com/case-studies/designing-eligibility-screener-montana-wic)

---

#### 2. Unemployment Insurance Claimant Support
**Context:** Nava has deep UI expertise from work with DOL, New Jersey, California, and Massachusetts. States are exploring AI to improve claimant experience.

**Use Case:** Help UI call center staff and claimant advocates connect unemployed workers with:
- Job training and certification programs
- Resume assistance and career counseling
- Emergency assistance (rent, utilities, food)
- Healthcare coverage (Medicaid, ACA marketplace)
- Childcare assistance for job seekers
- Transportation assistance for interviews

**Why It Fits:**
- Addresses high call volume challenges Nava has documented
- Supports "high-touch" claimants who need more than self-service
- Complements existing UI modernization work

**Sources:** [TCF: Can AI Improve UI?](https://tcf.org/content/commentary/can-ai-improve-americas-unemployment-safety-net-2/), [USDR: UI Modernization](https://www.usdigitalresponse.org/program-areas/unemployment-insurance)

---

#### 3. Integrated Benefits Enrollment (SNAP, Medicaid, TANF)
**Context:** Nava works with states on integrated eligibility and enrollment, including Vermont's IE&E system.

**Use Case:** Help benefits navigators at state/county offices connect applicants with full spectrum of services:
- Cross-program enrollment (SNAP → Medicaid → WIC → LIHEAP)
- Employment services for TANF recipients
- Childcare subsidies
- Healthcare providers accepting Medicaid
- Food resources beyond SNAP (food banks, community meals)
- Utility assistance programs

**Why It Fits:**
- Directly supports "no wrong door" policy goals
- Can reduce churn by connecting people to stabilizing services
- Builds on Nava's IE&E expertise

**Sources:** [Nava: Vermont IE&E](https://www.navapbc.com/case-studies/integrating-eligibility-enrollment-one-piece-software-time)

---

#### 4. Veterans Benefits Navigation
**Context:** Nava works extensively with VA on disability benefits and health outcomes.

**Use Case:** Help VA staff, VSOs, and community partners connect veterans with:
- Healthcare services (VA and community care)
- Mental health and PTSD support
- Housing programs (HUD-VASH, SSVF)
- Employment assistance for transitioning veterans
- Education benefits (GI Bill, Vet Tec)
- Caregiver support programs
- Legal assistance (discharge upgrades, benefits appeals)

**Why It Fits:**
- Existing VA relationship and deep domain knowledge
- Veterans often need cross-agency coordination
- High impact population with complex needs

**Sources:** [Nava VA Case Studies](https://www.navapbc.com/case-studies)

---

### Tier 2: Strong Alignment with Nava's Focus Areas

#### 5. Community Health Workers / Patient Navigators (SDOH)
**Context:** Healthcare systems increasingly screen for social determinants of health and need to connect patients with community resources.

**Use Case:** Help CHWs, care coordinators, and patient navigators address SDOH needs:
- Food security resources
- Housing stability services
- Transportation to medical appointments
- Utility assistance
- Mental health and substance abuse services
- Employment assistance
- Legal aid

**Why It Fits:**
- Aligns with Nava's healthcare work (CMS, perinatal care)
- Addresses documented challenge of "sticky note referrals"
- Closed-loop referral tracking is a key unmet need

**Tools in Market:** [Findhelp](https://company.findhelp.com), [Unite Us](https://uniteus.com), [Healthify](https://healthify.us)

---

#### 6. Coordinated Entry / Housing Navigation
**Context:** HUD requires Coordinated Entry for homeless services. Housing navigators match people to limited housing resources.

**Use Case:** Help housing navigators and coordinated entry assessors connect people experiencing homelessness with:
- Emergency shelter and transitional housing
- Rapid rehousing programs
- Permanent supportive housing
- Employment services
- Healthcare (including behavioral health)
- Document assistance (ID, birth certificate)
- Benefits enrollment

**Why It Fits:**
- Clear government mandate (HUD)
- Complex population needing cross-system coordination
- Current systems often use outdated resource directories

**Sources:** [HUD Exchange: Coordinated Entry](https://www.hudexchange.info/homelessness-assistance/coordinated-entry/), [KCRHA](https://kcrha.org/service-providers/about-coordinated-entry/)

---

#### 7. Aging & Disability Resource Centers (ADRCs)
**Context:** Area Agencies on Aging serve older adults and people with disabilities, helping them navigate complex service systems.

**Use Case:** Help Information & Referral specialists connect older adults and caregivers with:
- Home-delivered meals and nutrition programs
- In-home care and personal assistance
- Transportation services
- Medicare counseling (SHIP)
- Respite care for caregivers
- Adult day programs
- Long-term care options
- Fall prevention programs

**Why It Fits:**
- Federal funding through ACL
- Strong state/local government connection
- Growing need with aging population

**Sources:** [ACL: Area Agencies on Aging](https://acl.gov/programs/aging-and-disability-networks/area-agencies-aging)

---

### Tier 3: Adjacent Opportunities

#### 8. Reentry Services for Returning Citizens
**Context:** Second Chance Act funds programs to reduce recidivism. Returning citizens need coordinated support.

**Use Case:** Help reentry specialists and parole officers connect returning citizens with:
- Housing (many have restrictions due to record)
- Employment (ban-the-box employers)
- Substance abuse treatment
- Mental health services
- Education and job training
- Legal assistance (expungement, record sealing)
- Family reunification services

**Why It Fits:**
- Clear government role (DOJ, state corrections)
- High-stakes population where poor coordination leads to recidivism
- Niche resource knowledge needed (felony-friendly housing/employers)

**Sources:** [National Reentry Resource Center](https://nationalreentryresourcecenter.org/), [VOA Reentry Services](https://www.voa.org/services/community-justice-and-re-entry-services/)

---

#### 9. Public Library Social Services
**Context:** Libraries increasingly serve as community hubs where patrons seek help with social needs. Many now employ social workers.

**Use Case:** Help library staff and embedded social workers connect patrons with:
- Benefits enrollment assistance
- Housing resources
- Food assistance
- Healthcare
- Legal aid
- Employment services
- Domestic violence resources

**Why It Fits:**
- Libraries serve as trusted "no wrong door" entry point
- Staff currently use outdated binders or ad-hoc knowledge
- Lower barrier entry point than government offices

**Sources:** [Seattle Public Library Social Services](https://www.spl.org/programs-and-services/civics-and-social-services/social-services-referrals), [Findhelp: Libraries Partnership](https://company.findhelp.com/blog/2023/08/22/lifting-up-patrons-findhelp-and-libraries/)

---

#### 10. College Student Support Services
**Context:** Community colleges and universities have counselors helping students navigate academic and life challenges.

**Use Case:** Help academic advisors, student success coaches, and financial aid counselors connect students with:
- Emergency financial assistance
- Food pantries (campus and community)
- Housing resources (including emergency housing)
- Mental health services
- Childcare
- Transportation
- Tutoring and academic support
- Career services and internships

**Why It Fits:**
- State/local government funded institutions
- Students often eligible for benefits but don't know it
- Early alert systems can trigger proactive outreach

**Sources:** [Advisor.AI](https://joinadvisorai.com/), [E2E Advising](https://e2eadvising.com/)

---

## Evaluation Criteria for Prioritization

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Nava relationship exists | High | Easier entry, existing trust |
| State/local government customer | High | Aligns with Nava mission |
| Complex resource landscape | Medium | More value from AI matching |
| Volume of navigators | Medium | Scale opportunity |
| Clear funding stream | Medium | Sustainability |
| Regulatory driver | Medium | Mandated need |

---

## Recommended Next Steps

1. **Validate with Nava Labs team** - Which use cases align with current funding and partnerships?

2. **User research** - Interview 3-5 practitioners in top 2-3 use cases to understand:
   - Current workflow for resource referrals
   - Pain points with existing tools/processes
   - What "good" looks like

3. **Resource data availability** - For each use case, assess:
   - Is there a comprehensive resource directory?
   - How frequently does data change?
   - Who maintains it?

4. **Technical feasibility** - What modifications would the tool need?
   - Different category taxonomies
   - Domain-specific prompt tuning
   - Integration requirements (HMIS, EHR, MIS)

---

## Appendix: Market Landscape

### Existing Solutions by Category

**General Social Services:**
- [Findhelp (fka Aunt Bertha)](https://www.findhelp.org/) - Largest national resource directory
- [Unite Us](https://uniteus.com/) - Closed-loop referral platform
- [CaseWorthy](https://caseworthy.com/) - Case management with referrals

**Healthcare SDOH:**
- [Healthify](https://healthify.us/) - SDOH screening and referrals
- [NinePatch](https://ninepatch.com/) - Whole person care platform

**Government Case Management:**
- [myOneFlow](https://www.myoneflow.com/) - Government service delivery
- [Casebook](https://casebook.net/) - Child welfare and social services

**College Counseling:**
- [Scoir](https://www.scoir.com/) - College planning
- [Advisor.AI](https://joinadvisorai.com/) - Student success platform

### Differentiation Opportunity

The current tool's strengths that could differentiate in these markets:
1. **AI-generated justifications** - Explaining *why* a resource fits, not just *what* resources exist
2. **Action plan generation** - Going beyond referral to actionable next steps
3. **Natural language input** - Describing client needs in plain language vs. rigid forms
4. **Open source** - Government-friendly, auditable, customizable

---

## Creative Resource Types: Beyond Traditional Social Services

The tool's AI matching capabilities could extend far beyond traditional social service referrals. This section explores unconventional resource types that could dramatically expand the tool's value.

### Financial Resources

#### Grants & Funding Opportunities
**What it matches:** Government grants, foundation funding, small business programs, SBIR/STTR research grants

**Example:** A single mother wants to start a home daycare. The tool surfaces:
- SBA Community Navigator resources
- State childcare business grants
- Local CDFI microloans for women-owned businesses
- Foundation grants for early childhood providers

**Sources:** [SBA Grants](https://www.sba.gov/funding-programs/grants), [OpenGrants](https://opengrants.io/)

---

#### Scholarships & Education Funding
**What it matches:** College scholarships, trade school funding, workforce development grants, promise programs

**Example:** A 35-year-old veteran wants to retrain for IT. The tool surfaces:
- GI Bill benefits (if applicable)
- State promise programs for adults (Michigan Reconnect, MA MassEducate)
- IT-specific scholarships
- Employer tuition reimbursement programs

**Sources:** [Free College Promise Programs](https://www.freecollegenow.org/promise_programs), [ScholarshipOwl](https://scholarshipowl.com)

---

#### Tax Credits & Benefits
**What it matches:** EITC, Child Tax Credit, Child & Dependent Care Credit, state credits, VITA sites

**Example:** A working parent earning $35k doesn't know they qualify for $8,000+ in credits. The tool surfaces:
- EITC eligibility and estimated amount
- Child Tax Credit
- Dependent Care FSA options
- Free VITA tax prep locations
- State-specific credits

**Sources:** [Get It Back Campaign](https://www.taxoutreach.org/), [IRS Tax Credits](https://www.irs.gov/credits-deductions/individuals/child-tax-credit)

---

### Healthcare & Research

#### Clinical Trials
**What it matches:** Research studies, experimental treatments, paid trials

**Example:** A patient with treatment-resistant depression wants options beyond standard care. The tool surfaces:
- NIH-funded ketamine studies at local academic centers
- Psilocybin therapy trials
- Device trials (TMS, etc.)
- Compensation details and eligibility criteria

**Sources:** [NIH TrialGPT](https://www.nih.gov/news-events/news-releases/nih-developed-ai-algorithm-matches-potential-volunteers-clinical-trials), [ClinicalTrials.gov](https://clinicaltrials.gov)

---

#### Assistive Technology & Adaptive Equipment
**What it matches:** AT loan programs, vocational rehabilitation equipment, adaptive devices

**Example:** A person with low vision needs screen magnification for their new job. The tool surfaces:
- State AT loan program (0-3.5% interest)
- Vocational rehabilitation equipment funding
- Free device lending libraries to try before buying
- Specific product recommendations

**Sources:** [State AT Programs](https://catada.info/state.html), [Inclusive Inc AT Financing](https://inclusiveinc.org/pages/at-financing-loan)

---

### Legal Services

#### Pro Bono Legal Matching
**What it matches:** Volunteer attorneys, legal aid organizations, law school clinics

**Example:** A tenant facing illegal eviction needs representation. The tool surfaces:
- Local legal aid housing unit
- Pro bono eviction defense programs
- Tenant rights hotlines
- Law school housing clinics

**Sources:** [ABA Free Legal Help](https://www.americanbar.org/groups/legal_services/flh-home/flh-free-legal-help/), [Legal Aid Society NYC](https://legalaidnyc.org/)

---

#### Regulatory & Permit Navigation
**What it matches:** Business licensing help, permit assistance, compliance support

**Example:** A food truck operator needs help with health permits. The tool surfaces:
- State small business assistance office
- SBDC advisor appointments
- Health department permit requirements
- Local food entrepreneur programs

**Sources:** [SBA Licenses & Permits](https://www.sba.gov/business-guide/launch-your-business/apply-licenses-permits), [CalOSBA](https://calosba.ca.gov/)

---

### Housing Beyond Shelter

#### Community Land Trusts & Shared Equity
**What it matches:** CLT homeownership opportunities, limited equity co-ops, deed-restricted housing

**Example:** A family priced out of homeownership wants alternatives. The tool surfaces:
- Local community land trust with open applications
- Habitat for Humanity programs
- Shared equity down payment programs
- First-time homebuyer classes

**Sources:** [Grounded Solutions Network](https://groundedsolutions.org/strengthening-neighborhoods/community-land-trusts/), [HUD CLT Info](https://www.huduser.gov/portal/pdredge/pdr-edge-featd-article-110419.html)

---

### Community Exchange & Mutual Aid

#### Time Banks & Skill Sharing
**What it matches:** Time bank networks, skill exchange programs, community currencies

**Example:** A retiree with carpentry skills but limited income needs dental work. The tool surfaces:
- Local time bank where 1 hour of carpentry = 1 hour of any service
- Skills needed in the network (high demand for carpentry)
- Community members offering dental hygiene services

**Sources:** [hOurworld](https://hourworld.org/), [TimeBank Boulder](https://timebankboulder.org/)

---

#### Mutual Aid Networks
**What it matches:** Neighborhood pods, crisis funds, community support groups

**Example:** A family's car broke down and they need $400 for repairs to get to work. The tool surfaces:
- Local mutual aid emergency fund
- Neighborhood support pod
- Community car-sharing options
- Interest-free community loan funds

**Sources:** [Mutual Aid Hub](https://www.mutualaidhub.org/), [Mutual Aid NYC](https://mutualaid.nyc/)

---

### Workforce & Training

#### Apprenticeships & Trade Programs
**What it matches:** Registered apprenticeships, pre-apprenticeship programs, union training

**Example:** An 18-year-old wants to become an electrician. The tool surfaces:
- IBEW apprenticeship applications (next deadline)
- Pre-apprenticeship readiness programs
- Related community college programs
- Apprenticeship wage scales and benefits

**Sources:** [Apprenticeship.gov](https://www.apprenticeship.gov/career-seekers), [State Apprenticeship Agencies](https://www.apprenticeship.gov/partner-finder)

---

### Community Resources

#### Tool Libraries & Makerspaces
**What it matches:** Tool lending, community workshops, equipment access

**Example:** A new homeowner needs to install a fence but can't afford tools. The tool surfaces:
- Nearby tool library membership ($40/year for unlimited borrowing)
- Post hole digger, level, circular saw availability
- Weekend workshop on fence installation
- Community makerspace with woodworking equipment

**Sources:** [Denver Tool Library](https://denvertoollibrary.org/), [Tool Library Directory](https://en.wikipedia.org/wiki/Tool_library)

---

#### Repair Cafés & Fix-It Clinics
**What it matches:** Free repair events, volunteer fixers, skill-building opportunities

**Example:** A senior's vacuum cleaner stopped working. The tool surfaces:
- Next repair café date and location
- What to bring (vacuum, cord, etc.)
- Volunteer fixer expertise available
- Alternative: appliance repair vocational program that does low-cost repairs

**Sources:** [Repair Café International](https://www.repaircafe.org/en/), [Hennepin County Fix-It Clinics](https://www.hennepin.us/residents/recycling-hazardous-waste/fix-it-clinics)

---

#### Community Gardens & Urban Farming
**What it matches:** Garden plot availability, urban farms, food production training

**Example:** An apartment dweller wants to grow vegetables. The tool surfaces:
- Community garden with available plots (waitlist status)
- Urban farm volunteer opportunities (take home produce)
- Container gardening classes at library
- Seed library locations

**Sources:** [American Community Gardening Association](https://www.communitygarden.org/), [USDA Urban Agriculture](https://www.usda.gov/farming-and-ranching/agricultural-education-and-outreach/urban-agriculture-and-innovative-production)

---

### Specialized Needs

#### Diaper Banks & Baby Supplies
**What it matches:** Diaper distribution, baby supply banks, infant essentials

**Example:** A new parent on SNAP can't afford diapers. The tool surfaces:
- Local diaper bank distribution schedule
- Baby supply nonprofit (car seats, cribs, clothes)
- WIC enrollment (formula coverage)
- Cloth diaper lending program

**Sources:** [National Diaper Bank Network](https://nationaldiaperbanknetwork.org/), [Little Essentials](https://www.littleessentials.org/)

---

#### Pet Support for Low-Income Families
**What it matches:** Pet food banks, low-cost veterinary care, pet-friendly housing

**Example:** A senior on fixed income can't afford vet bills for their companion cat. The tool surfaces:
- Local pet food pantry
- Low-cost spay/neuter clinic
- Veterinary teaching hospital community fund
- Pet assistance grant applications

**Sources:** [Pets of the Homeless](https://petsofthehomeless.org/), [Best Friends Financial Assistance](https://bestfriends.org/pet-care-resources/cant-afford-vet-bills-100-financial-assistance-programs-pet-owners)

---

#### Furniture Banks & Household Goods
**What it matches:** Free furniture, household essentials, move-in kits

**Example:** A family exiting shelter has an apartment but no furniture. The tool surfaces:
- Furniture bank referral process
- What's available (beds, tables, kitchen items)
- Habitat ReStore for supplemental items
- Move-in kit programs

**Sources:** [Household Goods Inc](https://www.householdgoods.org/), [Habitat ReStore](https://www.habitat.org/restores)

---

#### Faith-Based Community Support
**What it matches:** Congregation benevolence funds, ministry programs, faith-based services

**Example:** A family needs emergency rent assistance. The tool surfaces:
- Local churches with benevolence funds (denominational and non-denominational)
- St. Vincent de Paul Society
- Salvation Army assistance
- Interfaith council emergency fund

**Sources:** [Faith-Based Organizations in Community Development (HUD)](https://www.huduser.gov/portal/publications/faithbased.pdf), [Casey Family Programs](https://www.casey.org/faith-based-organizations/)

---

#### Volunteer Driver Programs
**What it matches:** Medical appointment transportation, senior rides, disability transport

**Example:** An elderly patient needs rides to dialysis 3x/week. The tool surfaces:
- Area Agency on Aging volunteer driver program
- Faith-based transportation ministry
- American Cancer Society Road to Recovery (if applicable)
- Medicaid Non-Emergency Medical Transportation (NEMT)

**Sources:** [Connections to Care](https://connectionstocare.org/), [Ready Rides](https://readyrides.org/)

---

---

## Prioritized Opportunities for Nava PBC

This section maps use cases to Nava's actual government relationships and contract work, prioritized by strategic fit and impact potential.

### Nava's Current Portfolio (Context)

**Federal (~$100M+ in contracts):**
- **CMS**: Blue Button 2.0, Data Modernization, Medicare APIs (~$100M across contracts serving 63M+ beneficiaries)
- **VA**: Disability benefits, VA.gov, Caseflow appeals
- **HHS**: Grants.gov ($300B in annual grants)
- **DOL**: Unemployment insurance modernization
- **CDC**: ReportStream disease reporting

**State (active contracts):**
- **Massachusetts**: PFML, childcare assistance
- **Pennsylvania**: SNAP eligibility modernization
- **Nebraska**: Integrated benefits (iServe - SNAP, Medicaid)
- **Vermont**: Integrated eligibility & enrollment
- **New Jersey**: Unemployment insurance portal
- **Maryland**: 10-year agency modernization
- **California**: Unemployment, emergency assistance

---

### PRIORITY 1: Immediate Strategic Fit (Existing Relationships)

#### 1A. Medicare Beneficiary Resource Navigation
**Nava Relationship:** $100M+ in CMS contracts, Blue Button 2.0, serving 63M beneficiaries

**The Opportunity:** Medicare beneficiaries need help navigating not just healthcare, but the ecosystem of support services. CMS is increasingly focused on social determinants of health.

**Resources to Match:**
- Medicare Savings Programs (MSP) - help with Part B premiums
- Low Income Subsidy (Extra Help) - Part D drug costs
- State Pharmaceutical Assistance Programs (SPAPs)
- Area Agency on Aging services
- PACE programs
- Dual-eligible (Medicare-Medicaid) coordination
- Transportation to appointments
- Home modification programs
- Chronic disease management programs

**Why Now:**
- CMS pushing SDOH screening in Medicare Advantage
- ACO REACH model requires addressing social needs
- Nava already has the data relationships
- Natural extension of Blue Button/beneficiary tools

**Estimated Impact:** 63M Medicare beneficiaries, many unaware of supplemental benefits

---

#### 1B. Integrated Benefits Enrollment Expansion
**Nava Relationship:** Pennsylvania SNAP, Nebraska iServe, Vermont IE&E

**The Opportunity:** States with integrated eligibility systems need resource navigation beyond the programs they administer. When someone applies for SNAP, they likely need more than food assistance.

**Resources to Match:**
- Cross-program enrollment (SNAP → Medicaid → WIC → LIHEAP → TANF)
- Food banks and pantries (immediate need while SNAP processes)
- Utility assistance beyond LIHEAP
- Free tax prep (EITC, CTC)
- Childcare subsidies
- Healthcare providers accepting Medicaid
- Employment services
- Housing assistance

**Deployment Path:**
1. Pennsylvania SNAP pilot (existing relationship)
2. Nebraska iServe integration
3. Expand to other IE&E states

**Why Now:**
- Medicaid unwinding creating churn - people losing coverage need alternatives
- States looking for "no wrong door" solutions
- Can demonstrate value with existing contracts

---

#### 1C. Unemployment Insurance Claimant Support
**Nava Relationship:** DOL, New Jersey portal, California, Massachusetts

**The Opportunity:** UI claimants need more than unemployment checks. States struggle with call center volume and connecting people to workforce services.

**Resources to Match:**
- Job training and certification programs
- Resume and career counseling
- Emergency assistance (rent, utilities, food)
- Healthcare coverage (Medicaid, ACA)
- Childcare for job seekers
- Transportation assistance
- Mental health support
- Small business resources (for self-employment path)

**Why Now:**
- States still modernizing post-pandemic
- AI call center support is active DOL priority
- Nava has documented the user needs through prior research

---

#### 1D. Veterans Benefits Ecosystem
**Nava Relationship:** VA disability benefits, VA.gov, Caseflow

**The Opportunity:** Veterans often don't know what they qualify for beyond the benefit they're applying for. VA wants to improve the "whole veteran" experience.

**Resources to Match:**
- VA healthcare enrollment
- Community care providers
- Mental health and PTSD resources
- Caregiver support programs
- Education benefits (GI Bill, VET TEC)
- Housing (HUD-VASH, SSVF)
- Employment (VETS program, Hire Heroes)
- State veteran benefits (vary widely)
- VSO locations
- Vet Centers
- Legal assistance (discharge upgrades)

**Why Now:**
- VA actively investing in digital experience
- Nava positioned on key contracts
- High-impact, high-visibility population

---

### PRIORITY 2: Near-Term Expansion (Adjacent to Current Work)

#### 2A. Paid Family & Medical Leave Navigation
**Nava Relationship:** Massachusetts PFML (multiple contracts), PFML vendor partnerships in 3 states

**The Opportunity:** When someone takes PFML, they often need other support services - especially for medical leave situations.

**Resources to Match:**
- Healthcare providers and specialists
- Disability accommodations
- Mental health support
- Financial counseling
- Childcare (for new parents)
- Support groups (new parents, caregivers, chronic illness)
- Return-to-work programs
- ADA accommodation resources

**Unique Angle:** PFML is expanding rapidly - 13+ states now have programs. Nava could package this as part of their PFML implementation offering.

---

#### 2B. Grants.gov Applicant Support
**Nava Relationship:** HHS Grants.gov modernization ($300B annually)

**The Opportunity:** Grant seekers (nonprofits, researchers, state agencies) need help beyond finding grants - they need support for the application process.

**Resources to Match:**
- Grant writing training and technical assistance
- Fiscal sponsors for small organizations
- Compliance and audit support
- Matching fund sources
- Foundation grants (complementary to federal)
- SBDC and SCORE mentorship
- Research partnership opportunities

**Why Now:**
- Grants.gov modernization is active
- Could differentiate the platform
- Serves Nava's nonprofit/government ecosystem

---

#### 2C. Childcare Assistance Navigation (Massachusetts)
**Nava Relationship:** Massachusetts childcare financial assistance contract

**The Opportunity:** Families seeking childcare assistance need more than a voucher - they need help finding quality providers and stabilizing their situation.

**Resources to Match:**
- Licensed childcare providers with openings
- Head Start and Early Head Start
- After-school programs
- Summer programs
- WIC enrollment
- Family support services
- Early intervention services
- Parent education programs

---

### PRIORITY 3: Strategic Growth Opportunities

#### 3A. Medicaid Managed Care Navigation
**Context:** CMS relationship + state Medicaid work

**The Opportunity:** Medicaid managed care organizations (MCOs) are required to address SDOH but struggle with resource directories and closed-loop referrals.

**Business Model:** License tool to MCOs as part of their SDOH compliance, or partner with states to provide to MCOs.

**Market Size:** 70M+ Medicaid beneficiaries, MCOs spend billions on care coordination

---

#### 3B. 211 System Modernization
**Context:** 211 is the national social services hotline, but technology is fragmented and outdated

**The Opportunity:** Partner with United Way/211 networks to modernize their resource matching with AI.

**Why Nava:**
- Government trust and experience
- Open source approach appeals to nonprofit sector
- Could be philanthropically funded (like Nava Labs work)

---

#### 3C. State Aging Services (Area Agencies on Aging)
**Context:** ACL federal funding, state/local delivery

**The Opportunity:** 622 Area Agencies on Aging serve older adults but use outdated resource directories. This population overlaps heavily with Medicare.

**Synergy:** Combine with Medicare beneficiary work (Priority 1A) for comprehensive older adult support.

---

### Impact & Feasibility Matrix

| Opportunity | Strategic Fit | Existing Relationship | Market Size | Implementation Ease | **Priority Score** |
|-------------|--------------|----------------------|-------------|--------------------|--------------------|
| Medicare Beneficiary Navigation | ★★★★★ | ★★★★★ | 63M people | ★★★★☆ | **24/25** |
| Integrated Benefits (SNAP/Medicaid) | ★★★★★ | ★★★★★ | 40M+ households | ★★★★☆ | **24/25** |
| UI Claimant Support | ★★★★☆ | ★★★★☆ | Varies by economy | ★★★★☆ | **20/25** |
| Veterans Benefits | ★★★★☆ | ★★★★☆ | 18M veterans | ★★★☆☆ | **19/25** |
| PFML Navigation | ★★★★☆ | ★★★★★ | 13+ states | ★★★★☆ | **21/25** |
| Grants.gov Support | ★★★☆☆ | ★★★★★ | Niche | ★★★☆☆ | **17/25** |
| Childcare Assistance | ★★★★☆ | ★★★★☆ | State-specific | ★★★★☆ | **20/25** |
| Medicaid MCO | ★★★★★ | ★★★☆☆ | 70M people | ★★☆☆☆ | **18/25** |
| 211 Modernization | ★★★☆☆ | ★☆☆☆☆ | National | ★★☆☆☆ | **12/25** |
| Aging Services | ★★★★☆ | ★★☆☆☆ | 50M+ older adults | ★★★☆☆ | **16/25** |

---

### Recommended Pilot Sequence

**Phase 1 (Now - 6 months):** Leverage existing contracts
1. **Pennsylvania SNAP** - Add resource navigation to eligibility modernization work
2. **Massachusetts PFML** - Connect leave-takers to support services

**Phase 2 (6-12 months):** Expand within federal relationships
3. **CMS Medicare pilot** - Work with ACO or Medicare Advantage plan on beneficiary navigation
4. **VA integration** - Add resource navigation to disability benefits flow

**Phase 3 (12-18 months):** New market entry
5. **Medicaid MCO partnerships** - License to managed care organizations
6. **Additional state IE&E systems** - Package with integrated benefits work

---

### Resource Types Most Relevant to Nava's Work

Based on the priority use cases, these resource categories have the highest strategic value:

| Resource Category | Relevance to Nava Portfolio | Priority |
|------------------|----------------------------|----------|
| Healthcare providers (Medicaid/Medicare) | CMS, state Medicaid | ★★★★★ |
| Food assistance (SNAP, WIC, food banks) | State IE&E, WIC | ★★★★★ |
| Employment services | UI, TANF, VA | ★★★★★ |
| Housing assistance | Coordinated entry, VA | ★★★★☆ |
| Utility assistance (LIHEAP) | State IE&E | ★★★★☆ |
| Childcare subsidies | MA childcare, IE&E | ★★★★☆ |
| Tax credits (EITC, CTC) | Complements benefits work | ★★★★☆ |
| Mental health services | VA, PFML, healthcare | ★★★★☆ |
| Transportation | Medicare, aging, VA | ★★★☆☆ |
| Legal aid | VA, housing, benefits appeals | ★★★☆☆ |
| Grants & scholarships | Grants.gov adjacent | ★★☆☆☆ |
| Community resources (tool libraries, etc.) | Lower priority | ★☆☆☆☆ |

---

## Implications for Tool Design

### Data Architecture Expansion

To support these creative resource types, the tool would need:

| Resource Type | Data Source Challenge | Update Frequency |
|--------------|----------------------|------------------|
| Grants/Scholarships | Fragmented, deadline-driven | Weekly/Monthly |
| Clinical Trials | ClinicalTrials.gov API | Daily |
| Time Banks | Local networks, no aggregator | Manual partnership |
| Tool Libraries | No national directory | Annual |
| Repair Cafés | Event-based, scattered | Monthly |
| Community Gardens | City parks departments | Seasonal |
| Diaper Banks | NDBN member directory | Quarterly |

### Natural Language Advantages

The tool's NLP capabilities shine brightest with unconventional resources:

**Traditional search:** User must know to search for "community land trust" or "limited equity cooperative"

**AI-powered:** User says "I want to own a home but can't afford market prices" → tool surfaces CLTs, shared equity programs, Habitat for Humanity, down payment assistance

### Action Plan Differentiation

For creative resources, the action plan becomes even more valuable:

**Example action plan for time bank participation:**
1. Create profile on [Local Time Bank] - list your skills (carpentry, tutoring, etc.)
2. Browse available services you need
3. Attend new member orientation (next: Saturday 10am)
4. Start with a small exchange to build reputation
5. Connect with 3 members offering services you need

This level of guidance doesn't exist in any current resource directory.
