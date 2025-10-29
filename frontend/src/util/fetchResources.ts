import { Resource, ResourcesSchema } from "@/types/resources";

// TODO update the logic above to be ready for when we deploy to a PROD env
const generateReferralsURL =
  process.env.ENVIRONMENT == "local"
    ? "http://0.0.0.0:3000/generate_referrals/run"
    : "https://referral-pilot-dev.navateam.com/generate_referrals/run";

export async function fetchResources(
  clientDescription: string,
  prompt_version_id: string | null,
) {
  const url = generateReferralsURL;
  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 60_000); // TODO make configurable
  const requestBody = prompt_version_id
    ? JSON.stringify({
        query: clientDescription,
        prompt_version_id: prompt_version_id,
      })
    : JSON.stringify({ query: clientDescription });

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

    return { resultId: resultUuid, resources: resourcesAsArray };
  } catch {
    return { resultId: "", resources: [] };
  }
}
