import { z } from "zod";

export const ResourceSchema = z.object({
  name: z.string(),
  addresses: z.array(z.string()),
  phones: z.array(z.string()),
  emails: z.array(z.string().email()),
  website: z.string().url(),
  description: z.string(),
  justification: z.string(),
});

export const ResourcesSchema = z.object({
  resources: z.array(ResourceSchema),
});

export type Resource = z.infer<typeof ResourceSchema>;
export type Resources = z.infer<typeof ResourcesSchema>;

// TODO update the logic above to be ready for when we deploy to a PROD env
const generateReferralsURL =
  process.env.ENVIRONMENT == "dev"
    ? "https://referral-pilot-dev.navateam.com/generate_referrals/run"
    : "http://0.0.0.0:3000/generate_referrals/run";

export async function fetchResources(clientDescription: string) {
  const url = generateReferralsURL;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${process.env.EXTERNAL_API_KEY}`, // no NEXT_PUBLIC here   ---
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
    /* eslint-enable */

    return resources;
  } catch {
    return [];
  }
}
