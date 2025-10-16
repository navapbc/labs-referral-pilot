import { Resource, ResourcesSchema } from "@/types/resources";

// TODO update the logic above to be ready for when we deploy to a PROD env
const generateReferralsURL = process.env.ENVIRONMENT == "local"
    ? "http://0.0.0.0:3000/generate_referrals/run?prompt_version_id=UHJvbXB0VmVyc2lvbjoxMA=="
    : "https://referral-pilot-dev.navateam.com/generate_referrals/run";

export async function fetchResources(clientDescription: string) {
  const url = generateReferralsURL;
  const headers = {
    "Content-Type": "application/json",
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 30_000); // TODO make configurable

  try {
    const upstream = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({ query: clientDescription }),
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    /* eslint-disable */
    const responseData = await upstream.json(); // bypassing type enforcement due to heavy nesting within the API response
    const resourcesJson = JSON.parse(
      responseData.result.llm.replies[0]._content[0].text,
    );
    const resources = ResourcesSchema.parse(resourcesJson);
    const resourcesAsArray: Resource[] = resources.resources;
    /* eslint-enable */

    return resourcesAsArray;
  } catch {
    return [];
  }
}
