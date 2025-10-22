const emailResultURL =
  process.env.ENVIRONMENT == "local"
    ? "http://0.0.0.0:3000/email_result/run"
    : "https://p-51-app-dev-1362080447.us-east-1.elb.amazonaws.com/email_result/run";
    // FIXME: "https://referral-pilot-dev.navateam.com/email_result/run";

export async function emailResult(resultId: string, email: string) {
  const url = emailResultURL;
  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 30_000);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        result_id: resultId,
        email: email,
      }),
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || response.statusText);
    }

    const responseData = await response.json();
    const emailResultResponse = responseData.result.email_result;
    return { emailAddr: emailResultResponse.email, emailMessage: emailResultResponse.message };
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to send email");
  }
}
