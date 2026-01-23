import { Resource } from "@/types/resources";
import { getApiDomain } from "./apiDomain";
import { fixJsonControlCharacters, extractField } from "./parseStreamingUtils";

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
 * Parses streaming JSON to extract title, summary, and content fields
 * Handles incomplete JSON gracefully - captures partial strings even without closing quotes
 * Properly handles escaped characters like \", \n, etc.
 */
function parseStreamingJSON(jsonStr: string): PartialActionPlan {
  const title = extractField(jsonStr, "title") || "";
  const summary = extractField(jsonStr, "summary") || "";
  const content = extractField(jsonStr, "content") || "";

  return { title, summary, content };
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
    const requestBody: {
      resources: Resource[];
      user_email: string;
      user_query: string;
    } = {
      resources: resources,
      user_email: userEmail,
      user_query: userQuery,
    };

    const upstream = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(requestBody),
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
    let lastChunkContent = ""; // Track the last chunk to extract result_id

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
              // Store the last chunk content for result_id extraction
              lastChunkContent = content;

              // Only accumulate content that's not the result_id metadata
              if (!content.includes("result_id")) {
                // Accumulate the JSON content
                accumulatedJSON += content;

                // Parse incrementally and pass structured data to callback
                const partialPlan = parseStreamingJSON(accumulatedJSON);
                onChunk(partialPlan);
              }
            }

            // Check for finish_reason to detect completion
            if (parsed.choices?.[0]?.finish_reason === "stop") {
              // Extract result_id from the last chunk (the chunk before this stop message)
              if (!resultId && lastChunkContent.includes("result_id")) {
                try {
                  const resultIdData = JSON.parse(lastChunkContent) as {
                    result_id?: string;
                  };
                  if (resultIdData.result_id) {
                    resultId = resultIdData.result_id;
                  }
                } catch (e) {
                  console.error(
                    "Failed to extract result_id from last chunk:",
                    e,
                  );
                }
              }

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
