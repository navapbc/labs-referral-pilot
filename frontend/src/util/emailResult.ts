import { getApiDomain } from "./apiDomain";
import { ShareMode } from "@/components/ShareOptionsDialog";
import {
  ApiErrorResponse,
  EmailResultResponse,
  EmailFullResultResponse,
} from "@/types/api";
import { EMAIL_TIMEOUT } from "@/config/timeouts";


/**
 * Sends an email with resources, action plan, or both using the consolidated email_responses endpoint.
 *
 * @param resultId - ID of the resources result (optional if action plan provided)
 * @param actionPlanResultId - ID of the action plan result (optional if resources provided)
 * @param email - Recipient email address
 * @param mode - Share mode determining what content to include
 * @returns Promise with email address confirmation
 *
 * Scenarios:
 * - action-plan-only: Sends only the action plan
 * - full-referrals: Sends both resources and action plan
 * - default: Sends only resources
 */
export async function emailResult(
  resultId: string,
  actionPlanResultId: string | undefined,
  email: string,
  mode?: ShareMode,
) {
  const apiDomain =
    "https://p-179-app-dev-1778298227.us-east-1.elb.amazonaws.com/"; //await getApiDomain();

  // Use consolidated endpoint for all scenarios
  const endpoint = "email_responses";

  // Build request body based on mode - include only the relevant result IDs
  const body: Record<string, string> = { email };

  if (mode === "action-plan-only" && actionPlanResultId) {
    // Action plan only - don't include resources_result_id
    body.action_plan_result_id = actionPlanResultId;
  } else if (actionPlanResultId && mode !== "action-plan-only") {
    // Full referrals mode - include both IDs
    body.resources_result_id = resultId;
    body.action_plan_result_id = actionPlanResultId;
  } else {
    // Resources only - don't include action_plan_result_id
    body.resources_result_id = resultId;
  }

  const url = `${apiDomain}${endpoint}/run`;

  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), EMAIL_TIMEOUT); //300_000

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
        const errorData = (await response.json()) as ApiErrorResponse;
        // Try multiple possible error message fields
        errorMessage =
          errorData.message ||
          errorData.error ||
          errorData.detail ||
          errorData.result?.error ||
          errorData.result?.message ||
          `HTTP ${response.status}: ${response.statusText}`;
      } catch (e) {
        // If JSON parsing fails, use status text
        const errorStr = e instanceof Error ? e.message : String(e);
        errorMessage = `HTTP ${response.status}: ${response.statusText} (${errorStr})`;
      }

      throw new Error(errorMessage);
    }

    // Parse unified response from email_responses endpoint
    const responseData = (await response.json()) as EmailResponsesResponse;
    const emailAddress = responseData.result.email_responses.email;
    return { emailAddr: emailAddress };
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to send email");
  }
}
