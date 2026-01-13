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
  userQuery: string,
): Promise<{
  actionPlan: ActionPlan | null;
  resultId: string;
  errorMessage?: string;
}> {
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
 * Calls onChunk for each text chunk received, allowing progressive display.
 * Returns the same structure as fetchActionPlan for consistency.
 */
export async function fetchActionPlanStreaming(
  resources: Resource[],
  userEmail: string,
  userQuery: string,
  onChunk: (chunk: string) => void,
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
              onChunk(content);
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

    // Return success with result_id
    return {
      actionPlan: null, // ActionPlan will be constructed by the caller from accumulated content
      resultId: resultId,
      errorMessage: hasError ? errorMessage : undefined,
    };
  } catch (error) {
    clearTimeout(timer);
    let errMsg = "Unknown error occurred";

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        errMsg = "Request timed out, please try again.";
      } else {
        errMsg = error.message;
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
