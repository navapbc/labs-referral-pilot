import { Resource } from "@/types/resources";
import { getApiDomain } from "./apiDomain";
import {
  parseStreamingResources,
  PartialResource,
} from "./parseStreamingResources";
import { fixJsonControlCharacters } from "./parseStreamingUtils";
import { ResourcesSchema } from "@/types/resources";
import { createStreamingFetcher } from "./createStreamingFetcher";
import { STREAMING_TIMEOUT } from "@/config/timeouts";

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

  const result = await createStreamingFetcher<Resource[], PartialResource[]>({
    url,
    timeout: STREAMING_TIMEOUT, // 10 minutes
    requestBody,
    onChunk,
    onComplete,
    onError,
    shouldAccumulateContent: (content) => !content.includes("result_id"),
    parsePartial: (accumulatedJson) => {
      return parseStreamingResources(accumulatedJson);
    },
    parseFinal: (accumulatedJson) => {
      const fixedJson = fixJsonControlCharacters(accumulatedJson);
      const parsedData = JSON.parse(fixedJson) as unknown;
      const validatedData = ResourcesSchema.parse(parsedData);
      return validatedData.resources || [];
    },
  });

  // Check if resources array is empty
  if (!result.errorMessage && result.data && result.data.length === 0) {
    return {
      resultId: result.resultId,
      resources: [],
      errorMessage: "No Referrals Found",
    };
  }

  return {
    resources: result.data || [],
    resultId: result.resultId,
    errorMessage: result.errorMessage,
  };
}
