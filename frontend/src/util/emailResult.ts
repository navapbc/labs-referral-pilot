import { getApiDomain } from "./apiDomain";

export async function emailResult(
  resultId: string,
  actionPlanResultId: string | undefined,
  email: string,
) {
  const apiDomain = await getApiDomain();

  // Use email_full_result if actionPlanResultId is provided, otherwise use email_result
  const endpoint = actionPlanResultId ? "email_full_result" : "email_result";
  const url = `${apiDomain}${endpoint}/run`;

  const headers = {
    "Content-Type": "application/json",
  };

  // Build request body conditionally
  const body = actionPlanResultId
    ? {
        resources_result_id: resultId,
        action_plan_result_id: actionPlanResultId,
        email: email,
      }
    : {
        resources_result_id: resultId,
        email: email,
      };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 300_000);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      let errorMessage = response.statusText || "Unknown error";

      try {
        /* eslint-disable */
        const errorData = await response.json();
        // Try multiple possible error message fields
        errorMessage =
          errorData.message ||
          errorData.error ||
          errorData.detail ||
          errorData.result?.error ||
          errorData.result?.message ||
          `HTTP ${response.status}: ${response.statusText}`;
        /* eslint-enable */
      } catch (e) {
        // If JSON parsing fails, use status text
        const errorStr = e instanceof Error ? e.message : String(e);
        errorMessage = `HTTP ${response.status}: ${response.statusText} (${errorStr})`;
      }

      throw new Error(errorMessage);
    }

    /* eslint-disable */
    const responseData = await response.json();
    const emailAddress: string = responseData.result.email_result.email;
    /* eslint-enable */
    return { emailAddr: emailAddress };
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to send email");
  }
}
