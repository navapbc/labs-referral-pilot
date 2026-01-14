import { Resource, ResourcesSchema } from "@/types/resources";
import { getApiDomain } from "./apiDomain";

export async function fetchResources(
  clientDescription: string,
  userEmail: string,
  prompt_version_id: string | null,
) {
  const apiDomain = await getApiDomain();

  const useNonRag = process.env.NEXT_PUBLIC_USE_NONRAG === "true";
  const url_path = useNonRag
    ? "generate_referrals/run"
    : "generate_referrals_rag/run";

  const url = apiDomain + url_path;
  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 600_000); // TODO make configurable

  const requestData: {
    query: string;
    user_email: string;
    prompt_version_id?: string;
    suffix?: string;
  } = {
    query: clientDescription,
    user_email: userEmail,
  };

  if (prompt_version_id) {
    requestData.prompt_version_id = prompt_version_id;
  }

  if (suffix) {
    requestData.suffix = suffix;
  }

  const requestBody = JSON.stringify(requestData);

  try {
    const upstream = await fetch(url, {
      method: "POST",
      headers,
      body: requestBody,
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    /* eslint-disable */
    const responseData = await upstream.json(); // bypassing type enforcement due to heavy nesting within the API response
    const resultUuid: string = responseData.result.save_result.result_id;

    console.log(responseData);

    const resourcesJson = JSON.parse(
      responseData.result.llm.replies[0]._content[0].text,
    );

    console.log(resourcesJson);

    const resources = ResourcesSchema.parse(resourcesJson);
    const resourcesAsArray: Resource[] = resources.resources || [];

    console.log(resourcesAsArray);

    /* eslint-enable */

    // Check if resources array is empty
    if (resourcesAsArray.length === 0) {
      return {
        resultId: resultUuid,
        resources: [],
        errorMessage: "The API did not return any resource recommendations.",
      };
    }

    // Success, return result
    return {
      resultId: resultUuid,
      resources: resourcesAsArray,
    };
  } catch (error) {
    clearTimeout(timer);
    // Check if the error is due to timeout
    if (error instanceof Error && error.name === "AbortError") {
      return {
        resultId: "",
        resources: [],
        errorMessage: "Request timed out, please try again.",
      };
    }
  }

  // Generic error handling
  return {
    resultId: "",
    resources: [],
    errorMessage:
      "The server encountered an unexpected error. Please try again later.",
  };
}
