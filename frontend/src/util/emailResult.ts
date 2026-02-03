import { getApiDomain } from "./apiDomain";
import {
  ApiErrorResponse,
  EmailResultResponse,
  EmailFullResultResponse,
  EmailActionPlanResponse,
} from "@/types/api";
import { ShareMode } from "@/components/ShareOptionsDialog";

export async function emailResult(
  resultId: string,
  actionPlanResultId: string | undefined,
  email: string,
  mode?: ShareMode,
) {
  const apiDomain = await getApiDomain();

  // Determine endpoint and body based on mode
  let endpoint: string;
  let body: Record<string, string>;

  if (mode === "action-plan-only" && actionPlanResultId) {
    // Action plan only mode - use new endpoint
    endpoint = "email_action_plan";
    body = {
      action_plan_result_id: actionPlanResultId,
      email: email,
    };
  } else if (actionPlanResultId && mode !== "action-plan-only") {
    // Full referrals mode with action plan - use email_full_result
    endpoint = "email_full_result";
    body = {
      resources_result_id: resultId,
      action_plan_result_id: actionPlanResultId,
      email: email,
    };
  } else {
    // Resources only (no action plan)
    endpoint = "email_result";
    body = {
      resources_result_id: resultId,
      email: email,
    };
  }

  const url = `${apiDomain}${endpoint}/run`;

  const headers = {
    "Content-Type": "application/json",
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

    // Parse response based on endpoint
    let emailAddress: string;
    if (endpoint === "email_action_plan") {
      const responseData = (await response.json()) as EmailActionPlanResponse;
      emailAddress = responseData.result.email_action_plan.email;
    } else if (endpoint === "email_full_result") {
      const responseData = (await response.json()) as EmailFullResultResponse;
      emailAddress = responseData.result.email_full_result.email;
    } else {
      const responseData = (await response.json()) as EmailResultResponse;
      emailAddress = responseData.result.email_result.email;
    }
    return { emailAddr: emailAddress };
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to send email");
  }
}
