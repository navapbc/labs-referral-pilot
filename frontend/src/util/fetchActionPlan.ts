import { Resource } from "@/types/resources";

export interface ActionPlan {
  title: string;
  summary: string;
  content: string;
}

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

const generateActionPlanURL = "http://0.0.0.0:3000/generate_action_plan/run";  // TODO MRH revert
  /*process.env.ENVIRONMENT === "local"
    ? "http://0.0.0.0:3000/generate_action_plan/run"
    : "https://referral-pilot-dev.navateam.com/generate_action_plan/run";*/

export async function fetchActionPlan(
  resources: Resource[],
): Promise<ActionPlan | null> {
  const url = generateActionPlanURL;
  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 240_000); // TODO MRH update or reomve

  try {
    const upstream = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({ resources }),
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!upstream.ok) {
      console.error("Failed to generate action plan:", upstream.statusText);
      return null;
    }

    /* eslint-disable */
    const responseData = await upstream.json();
    // Extract the action plan from the API response
    const actionPlanText = responseData.result.llm.replies[0]._content[0].text;
    console.log("Raw action plan text:", actionPlanText);

    // The LLM likes to return a multi-line JSON string, so
    // escape these characters or JSON.parse will fail
    const fixedJson = fixJsonControlCharacters(actionPlanText);
    const actionPlan = JSON.parse(fixedJson);
    /* eslint-enable */

    return actionPlan as ActionPlan;
  } catch (error) {
    console.error("Error fetching action plan:", error);
    return null;
  }
}
