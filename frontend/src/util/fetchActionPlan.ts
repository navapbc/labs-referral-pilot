import { Resource } from "@/types/resources";
import { getApiDomain } from "./apiDomain";

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

    // Generic error handling
    console.error("Error fetching action plan:", error);
    return {
      actionPlan: null,
      errorMessage:
        "The server encountered an unexpected error. Please try again later.",
    };
  }
}
