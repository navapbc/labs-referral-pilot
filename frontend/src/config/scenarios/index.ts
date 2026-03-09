import { Resource } from "@/types/resources";

export interface ResourceCategory {
  id: string;
  label: string;
  emoji: string;
}

export interface ProviderType {
  id: string;
  label: string;
  emoji?: string;
  logoSrc?: string;
}

export interface MockActionPlan {
  title: string;
  summary: string;
  content: string;
}

export interface ScenarioConfig {
  id: string;
  name: string;
  tagline: string;
  logoSrc?: string;
  logoEmoji?: string;
  primaryColor: string;
  categories: ResourceCategory[];
  providerTypes: ProviderType[];
  sampleClientDescription: string;
  sampleLocation: string;
  mockResources: Resource[];
  mockActionPlan?: MockActionPlan;
  placeholderText: string;
}

// Import all scenarios
import { defaultScenario } from "./default";
import { medicareScenario } from "./medicare";
import { snapScenario } from "./snap";
import { unemploymentScenario } from "./unemployment";
import { veteransScenario } from "./veterans";
import { pfmlScenario } from "./pfml";

export const scenarios: Record<string, ScenarioConfig> = {
  default: defaultScenario,
  medicare: medicareScenario,
  snap: snapScenario,
  unemployment: unemploymentScenario,
  veterans: veteransScenario,
  pfml: pfmlScenario,
};

export function getScenario(scenarioId: string | null): ScenarioConfig {
  if (!scenarioId || !scenarios[scenarioId]) {
    return scenarios.default;
  }
  return scenarios[scenarioId];
}

export {
  defaultScenario,
  medicareScenario,
  snapScenario,
  unemploymentScenario,
  veteransScenario,
  pfmlScenario,
};
