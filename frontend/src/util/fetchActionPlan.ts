import { Resource } from "@/types/resources";
import { getApiDomain } from "./apiDomain";

export interface ActionPlan {
  title: string;
  summary: string;
  content: string;
}

export interface PartialActionPlan {
  title: string;
  summary: string;
  content: string;
}

/**
 * Unescapes JSON string escape sequences
 */
function unescapeJSON(str: string): string {
  return str
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "\r")
    .replace(/\\t/g, "\t")
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, "\\");
}

/**
 * Parses streaming JSON to extract title, summary, and content fields
 * Handles incomplete JSON gracefully - captures partial strings even without closing quotes
 * Properly handles escaped characters like \", \n, etc.
 */
function parseStreamingJSON(jsonStr: string): PartialActionPlan {
  let title = "";
  let summary = "";
  let content = "";

  try {
    // Pattern that matches escaped characters: (?:[^"\\]|\\.)*
    // - [^"\\] matches any char except quote or backslash
    // - \\. matches backslash followed by any char (handles \", \n, etc)

    // Extract title - try complete first, then incomplete
    const titleMatch = jsonStr.match(/"title"\s*:\s*"((?:[^"\\]|\\.)*)"/);
    if (titleMatch) {
      title = unescapeJSON(titleMatch[1]);
    } else {
      // Match incomplete title (no closing quote yet)
      const incompleteTitleMatch = jsonStr.match(
        /"title"\s*:\s*"((?:[^"\\]|\\.)*)/,
      );
      if (incompleteTitleMatch) {
        title = unescapeJSON(incompleteTitleMatch[1]);
      }
    }

    // Extract summary - same approach
    const summaryMatch = jsonStr.match(/"summary"\s*:\s*"((?:[^"\\]|\\.)*)"/);
    if (summaryMatch) {
      summary = unescapeJSON(summaryMatch[1]);
    } else {
      const incompleteSummaryMatch = jsonStr.match(
        /"summary"\s*:\s*"((?:[^"\\]|\\.)*)/,
      );
      if (incompleteSummaryMatch) {
        summary = unescapeJSON(incompleteSummaryMatch[1]);
      }
    }

    // Extract content - this is where word-by-word streaming matters most
    const contentMatch = jsonStr.match(/"content"\s*:\s*"((?:[^"\\]|\\.)*)"/);
    if (contentMatch) {
      content = unescapeJSON(contentMatch[1]);
    } else {
      // Match incomplete content (no closing quote yet) - this enables word-by-word rendering
      const incompleteContentMatch = jsonStr.match(
        /"content"\s*:\s*"((?:[^"\\]|\\.)*)/,
      );
      if (incompleteContentMatch) {
        content = unescapeJSON(incompleteContentMatch[1]);
      }
    }
  } catch (e) {
    console.error("Error parsing streaming JSON:", e);
  }

  return { title, summary, content };
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
  userQuery: string,
): Promise<{
  actionPlan: ActionPlan | null;
  resultId: string;
  errorMessage?: string;
}> {
  const apiDomain = "https://p-140-app-dev-165284618.us-east-1.elb.amazonaws.com/" // TODO REVERT - await getApiDomain();
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
        user_query: userQuery,
      }),
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!upstream.ok) {
      console.error("Failed to generate action plan:", upstream.statusText);
      return {
        actionPlan: null,
        resultId: "",
        errorMessage:
          "The server encountered an unexpected error. Please try again later.",
      };
    }

    /* eslint-disable */
    const responseData = await upstream.json();
    // Extract the result ID from the API response
    const resultUuid: string = responseData.result.save_result.result_id;
    // Extract the action plan from the API response
    const actionPlanText = responseData.result.response;
    console.log("Raw action plan text:", actionPlanText);

    // The LLM likes to return a multi-line JSON string, so
    // escape these characters or JSON.parse will fail
    const fixedJson = fixJsonControlCharacters(actionPlanText);
    const actionPlan = JSON.parse(fixedJson);
    /* eslint-enable */

    return { actionPlan: actionPlan as ActionPlan, resultId: resultUuid };
  } catch (error) {
    clearTimeout(timer);
    // Check if the error is due to timeout
    if (error instanceof Error && error.name === "AbortError") {
      return {
        actionPlan: null,
        resultId: "",
        errorMessage: "Request timed out, please try again.",
      };
    }
  }
  // Generic error handling
  console.error("Error fetching action plan");
  clearTimeout(timer);
  return {
    actionPlan: null,
    resultId: "",
    errorMessage:
      "The server encountered an unexpected error. Please try again later.",
  };
}

/**
 * Fetches action plan with streaming support using Server-Sent Events (SSE).
 * Calls onChunk with parsed structured data for progressive display.
 * Returns the same structure as fetchActionPlan for consistency.
 */
export async function fetchActionPlanStreaming(
  resources: Resource[],
  userEmail: string,
  userQuery: string,
  onChunk: (partialPlan: PartialActionPlan) => void,
  onComplete: () => void,
  onError: (error: string) => void,
): Promise<{
  actionPlan: ActionPlan | null;
  resultId: string;
  errorMessage?: string;
}> {
  const apiDomain = await getApiDomain();
  // Use the standard chat completions endpoint with pipeline name as model
  const url = `${apiDomain}chat/completions`;

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 600_000); // 10 minutes timeout

  let resultId = "";
  let hasError = false;
  let errorMessage: string | undefined;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "generate_action_plan", // Pipeline name as model
        messages: [{ role: "user", content: userQuery }],
        stream: true,
        resources: resources,
        user_email: userEmail,
        user_query: userQuery,
      }),
      signal: ac.signal,
    });

    if (!response.ok) {
      clearTimeout(timer);
      const errMsg = `Request failed with status ${response.status}`;
      onError(errMsg);
      return {
        actionPlan: null,
        resultId: "",
        errorMessage: errMsg,
      };
    }

    // Check for result_id in response headers
    const headerResultId = response.headers.get("x-result-id");
    if (headerResultId) {
      resultId = headerResultId;
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      clearTimeout(timer);
      const errMsg = "Response body is null";
      onError(errMsg);
      return {
        actionPlan: null,
        resultId: "",
        errorMessage: errMsg,
      };
    }

    let buffer = "";
    let accumulatedJSON = ""; // Accumulate the full JSON response

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        clearTimeout(timer);
        onComplete();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      // Keep last incomplete line in buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();

          if (data === "[DONE]" || !data) {
            continue;
          }

          try {
            const parsed = JSON.parse(data) as {
              error?: string;
              result_id?: string;
              choices?: Array<{
                delta?: { content?: string };
                finish_reason?: string;
              }>;
            };

            // Check for error in the response
            if (parsed.error) {
              clearTimeout(timer);
              hasError = true;
              errorMessage = parsed.error;
              onError(parsed.error);
              return {
                actionPlan: null,
                resultId: "",
                errorMessage: parsed.error,
              };
            }

            // Extract result_id if present (may come in metadata)
            if (parsed.result_id) {
              resultId = parsed.result_id;
            }

            // Handle hayhooks response format: choices[0].delta.content
            const content = parsed.choices?.[0]?.delta?.content;
            if (content) {
              // Accumulate the JSON content
              accumulatedJSON += content;

              // Parse incrementally and pass structured data to callback
              const partialPlan = parseStreamingJSON(accumulatedJSON);
              onChunk(partialPlan);
            }

            // Check for finish_reason to detect completion
            if (parsed.choices?.[0]?.finish_reason === "stop") {
              clearTimeout(timer);
              onComplete();
              break;
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e, data);
          }
        }
      }
    }

    // Parse the final accumulated JSON to get complete ActionPlan
    let finalActionPlan: ActionPlan | null = null;

    if (!hasError && accumulatedJSON) {
      try {
        // Try to parse the complete JSON response
        const fixedJson = fixJsonControlCharacters(accumulatedJSON);
        finalActionPlan = JSON.parse(fixedJson) as ActionPlan;
      } catch (e) {
        console.error("Failed to parse final action plan JSON:", e);
        console.error("Raw accumulated JSON:", accumulatedJSON);
        errorMessage =
          "Failed to parse the action plan response. Please try again.";
        hasError = true;
        onError(errorMessage);
      }
    }

    // Return success with result_id and parsed action plan
    return {
      actionPlan: finalActionPlan,
      resultId: resultId,
      errorMessage: hasError ? errorMessage : undefined,
    };
  } catch (error) {
    clearTimeout(timer);
    let errMsg =
      "There was an issue streaming the Action Plan. Please try again.";

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        errMsg = "Request timed out. Please try again.";
      } else {
        errMsg =
          "There was an issue streaming the Action Plan. Please try again.";
      }
    }

    onError(errMsg);
    return {
      actionPlan: null,
      resultId: "",
      errorMessage: errMsg,
    };
  }
}
