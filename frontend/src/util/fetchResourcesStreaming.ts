import { Resource } from "@/types/resources";
import { getApiDomain } from "./apiDomain";
import {
  parseStreamingResources,
  PartialResource,
} from "./parseStreamingResources";
import { fixJsonControlCharacters } from "./parseStreamingUtils";
import { ResourcesSchema } from "@/types/resources";

/**
 * Fetches resources with streaming support using Server-Sent Events (SSE).
 * Calls onChunk with parsed partial resources for progressive display.
 */
export async function fetchResourcesStreaming(
  clientDescription: string,
  userEmail: string,
  onChunk: (partialResources: PartialResource[]) => void,
  onComplete: () => void,
  onError: (error: string) => void,
  prompt_version_id?: string | null,
  suffix?: string,
): Promise<{
  resources: Resource[];
  resultId: string;
  errorMessage?: string;
}> {
  const apiDomain = await getApiDomain();
  const useNonRag = process.env.NEXT_PUBLIC_USE_NONRAG === "true";
  const model = useNonRag ? "generate_referrals" : "generate_referrals_rag";

  // Use the chat completions endpoint with pipeline name as model
  const url = `${apiDomain}chat/completions`;

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 600_000); // 10 minutes timeout

  let resultId = "";
  let hasError = false;
  let errorMessage: string | undefined;

  try {
    const requestBody: {
      model: string;
      messages: Array<{ role: string; content: string }>;
      stream: boolean;
      user_email: string;
      query: string;
      prompt_version_id?: string;
      suffix?: string;
    } = {
      model: model,
      messages: [{ role: "user", content: clientDescription }],
      stream: true,
      user_email: userEmail,
      query: clientDescription,
    };

    if (prompt_version_id) {
      requestBody.prompt_version_id = prompt_version_id;
    }

    if (suffix) {
      requestBody.suffix = suffix;
    }

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
      signal: ac.signal,
    });

    if (!response.ok) {
      clearTimeout(timer);
      const errMsg = `Request failed with status ${response.status}`;
      onError(errMsg);
      return {
        resources: [],
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
        resources: [],
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
        reader.releaseLock();
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
                resources: [],
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
                const partialResources =
                  parseStreamingResources(accumulatedJSON);
                onChunk(partialResources);
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

    // Parse the final accumulated JSON to get complete Resources
    let finalResources: Resource[] = [];

    if (!hasError && accumulatedJSON) {
      try {
        // Try to parse the complete JSON response
        const fixedJson = fixJsonControlCharacters(accumulatedJSON);
        const parsedData = JSON.parse(fixedJson) as unknown;
        const validatedData = ResourcesSchema.parse(parsedData);
        finalResources = validatedData.resources || [];
      } catch (e) {
        console.error("Failed to parse final resources JSON:", e);
        console.error("Raw accumulated JSON:", accumulatedJSON);
        errorMessage =
          "Failed to parse the resources response. Please try again.";
        hasError = true;
        onError(errorMessage);
      }
    }

    // Check if resources array is empty
    if (!hasError && finalResources.length === 0) {
      return {
        resultId: resultId,
        resources: [],
        errorMessage: "No Referrals Found",
      };
    }

    // Return success with result_id and parsed resources
    return {
      resources: finalResources,
      resultId: resultId,
      errorMessage: hasError ? errorMessage : undefined,
    };
  } catch (error) {
    clearTimeout(timer);
    let errMsg =
      "The server encountered an unexpected error. Please try again later.";

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        errMsg = "Request timed out, please try again.";
      } else {
        errMsg =
          "The server encountered an unexpected error. Please try again later.";
      }
    }

    onError(errMsg);
    return {
      resources: [],
      resultId: "",
      errorMessage: errMsg,
    };
  }
}
