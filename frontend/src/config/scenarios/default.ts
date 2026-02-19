import { ScenarioConfig } from "./index";

export const defaultScenario: ScenarioConfig = {
  id: "default",
  name: "Find Resources",
  tagline: "GenAI Referral Tool",
  logoSrc: "/img/Goodwill_Industries_Logo.svg",
  primaryColor: "blue",
  categories: [
    { id: "childcare", label: "Childcare", emoji: "👶" },
    { id: "disability", label: "Disability Services", emoji: "♿" },
    { id: "education", label: "Education & GED", emoji: "🎓" },
    { id: "employment", label: "Employment & Job Training", emoji: "💼" },
    { id: "financial", label: "Financial Assistance", emoji: "💵" },
    { id: "food", label: "Food Assistance", emoji: "🍽️" },
    { id: "healthcare", label: "Healthcare & Mental Health", emoji: "🩺" },
    { id: "housing", label: "Housing & Shelter", emoji: "🏠" },
    { id: "legal", label: "Legal Services", emoji: "⚖️" },
    { id: "substance", label: "Substance Use & Treatment", emoji: "🛡️" },
    { id: "transportation", label: "Transportation", emoji: "🚗" },
    { id: "veterans", label: "Veterans Services", emoji: "🎖️" },
  ],
  providerTypes: [
    {
      id: "goodwill",
      label: "Goodwill",
      logoSrc: "/img/Goodwill_Industries_Logo.svg",
    },
    { id: "government", label: "Government", emoji: "🏛️" },
    { id: "community", label: "Community", emoji: "👥" },
  ],
  sampleClientDescription:
    "My client is looking for medical assistant training, diapers and clothes for job interviews.",
  sampleLocation: "Austin, TX",
  placeholderText:
    "Example: My client is looking for medical assistant training, diapers and clothes for job interviews.",
  mockResources: [
    {
      name: "Goodwill Career Center - Central Austin",
      addresses: ["1015 Norwood Park Blvd, Austin, TX 78753"],
      phones: ["(512) 637-7100"],
      emails: ["careers@goodwillcentraltexas.org"],
      website: "https://www.goodwillcentraltexas.org/jobs-training",
      description:
        "Provides job training, career counseling, resume assistance, and professional clothing for interviews.",
      justification:
        "Offers medical assistant training programs and can provide interview clothing through their career services.",
      referral_type: "goodwill",
    },
    {
      name: "Workforce Solutions Capital Area",
      addresses: ["6505 Airport Blvd, Suite 101, Austin, TX 78752"],
      phones: ["(512) 597-7100"],
      website: "https://www.wfscapitalarea.com",
      description:
        "State workforce development agency providing job training, career services, and childcare assistance.",
      justification:
        "Can fund healthcare training programs and connect client with additional support services.",
      referral_type: "government",
    },
    {
      name: "Austin Diaper Bank",
      addresses: ["2001 E Martin Luther King Jr Blvd, Austin, TX 78702"],
      phones: ["(512) 693-9500"],
      website: "https://austindiaperbank.org",
      description:
        "Provides free diapers and baby supplies to families in need through partner agencies.",
      justification:
        "Direct source for diapers mentioned in client needs. Can provide ongoing supply while client is in training.",
      referral_type: "external",
    },
  ],
};
