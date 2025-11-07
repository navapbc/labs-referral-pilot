import { Resource } from "@/types/resources";
import { getApiDomain } from "./apiDomain";

export interface ActionPlan {
  title: string;
  summary: string;
  content: string;
}

export const sampleActionPlan: ActionPlan = {
  title: "Expunge your record after fulfilling probation requirements",
  summary:
    "Having a clean record will help you in your job application process.",
  content:
    "### Project RIO\\n**How to apply:**\\n- Call the Project RIO line and ask for the Austin office: 1-800-453-8140. ([hrw.org](https://www.hrw.org/news/2010/07/20/texas-prison-resources?utm_source=openai))\\n- Visit or mail to the TWC Project RIO office at 101 East 15th Street, Room 506-T, Austin, TX 78778 to set an intake appointment. ([hrw.org](https://www.hrw.org/news/2010/07/20/texas-prison-resources?utm_source=openai))\\n\\n**Documents needed:**\\n- Photo ID (state ID or driver’s license)\\n- Proof of release/parole papers or probation completion\\n- Social Security card or number\\n- Recent resume or list of past jobs (if available)\\n\\n**Timeline:**\\n- First appointment often same week to 2 weeks.\\n\\n**Key tip:**\\n- Tell staff you are eligible for employer incentives (Work Opportunity Tax Credit). Project RIO staff can connect you to employers and note hiring incentives. ([ojp.gov](https://www.ojp.gov/ncjrs/virtual-library/abstracts/project-rio-procedures-and-reporting-manual?utm_source=openai))\\n",
};

/**
 * Fixes unescaped control characters in JSON string values
 * This handles cases where the LLM returns JSON with literal newlines, tabs, etc.
 */
function fixJsonControlCharacters(jsonString: string): string {
  let inString = false;
  let result = "";
  let prevChar = "";

  for (let i = 0; i < jsonString.length; i++) {
    const currentChar = jsonString[i];

    // Toggle string state when we hit an unescaped quote
    if (currentChar === '"' && prevChar !== "\\") {
      inString = !inString;
      result += currentChar;
    } else if (inString) {
      // Inside a string value - escape control characters
      if (currentChar === "\n") {
        result += "\\n";
      } else if (currentChar === "\r") {
        result += "\\r";
      } else if (currentChar === "\t") {
        result += "\\t";
      } else if (currentChar === "\b") {
        result += "\\b";
      } else if (currentChar === "\f") {
        result += "\\f";
      } else {
        result += currentChar;
      }
    } else {
      // Outside string values - keep as is
      result += currentChar;
    }

    prevChar = currentChar;
  }

  return result;
}

export async function fetchActionPlan(
  resources: Resource[],
  userEmail: string,
): Promise<{ actionPlan: ActionPlan | null; errorMessage?: string }> {
  const apiDomain = await getApiDomain();
  const url = apiDomain + "generate_action_plan/run";
  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 120_000);

  try {
    const upstream = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        resources: resources,
        user_email: userEmail,
      }),
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!upstream.ok) {
      console.error("Failed to generate action plan:", upstream.statusText);
      return {
        actionPlan: null,
        errorMessage:
          "The server encountered an unexpected error. Please try again later.",
      };
    }

    /* eslint-disable */
    const responseData = await upstream.json();
    // Extract the action plan from the API response
    const actionPlanText = responseData.result.response;
    console.log("Raw action plan text:", actionPlanText);

    // The LLM likes to return a multi-line JSON string, so
    // escape these characters or JSON.parse will fail
    const fixedJson = fixJsonControlCharacters(actionPlanText);
    const actionPlan = JSON.parse(fixedJson);
    /* eslint-enable */

    return { actionPlan: actionPlan as ActionPlan };
  } catch (error) {
    clearTimeout(timer);
    // Check if the error is due to timeout
    if (error instanceof Error && error.name === "AbortError") {
      return {
        actionPlan: null,
        errorMessage: "Request timed out, please try again.",
      };
    }
  }
  // Generic error handling
  console.error("Error fetching action plan");
  clearTimeout(timer);
  return {
    actionPlan: null,
    errorMessage:
      "The server encountered an unexpected error. Please try again later.",
  };
}
